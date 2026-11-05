"""Serve the page and ask Cursor to explain words in the lecture's context."""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
NOTES_DIR = ROOT / "notes"
SEOUL = ZoneInfo("Asia/Seoul")
FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
UNSAFE = re.compile(r'[\\/:*?"<>|]+')
_ASK_LOCK = threading.Lock()


def load_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()


def api_key() -> str:
    return os.environ.get("CURSOR_API_KEY", "").strip()


def model_id() -> str:
    return os.environ.get("CURSOR_MODEL", "").strip() or "composer-2.5"


def ask_model(prompt: str) -> str:
    key = api_key()
    if not key:
        raise RuntimeError("CURSOR_API_KEY가 없습니다. lecture-words/.env 에 넣어 주세요.")
    from cursor_sdk import Agent, AgentOptions, LocalAgentOptions

    from sdk_windows import configure_bridge_tls, install_windows_bridge

    configure_bridge_tls()
    install_windows_bridge()
    with _ASK_LOCK:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=key,
                model=model_id(),
                tools=[],
                local=LocalAgentOptions(cwd=str(ROOT)),
            ),
        )
    if getattr(result, "status", "") == "error":
        raise RuntimeError(getattr(result, "result", None) or "모델 실행에 실패했습니다.")
    text = (getattr(result, "result", None) or "").strip()
    if not text:
        raise RuntimeError("모델이 빈 답을 보냈습니다.")
    return text


def extract_json(text: str):
    blob = text.strip()
    fenced = FENCE.search(blob)
    if fenced:
        blob = fenced.group(1).strip()
    start = blob.find("[")
    end = blob.rfind("]")
    if start < 0 or end <= start:
        raise ValueError("JSON 배열이 없습니다.")
    return json.loads(blob[start : end + 1])


def concepts_prompt(lecture: str) -> str:
    return f"""너는 강의 조교다. 수업 주제는 아래와 같다.

수업: {lecture}

이 수업에서 처음 몇 주에 자주 나오는 핵심 용어 8개를 고른다.
백과사전 일반 주제가 아니라 이 수업 시간에 칠판에 적힐 말을 고른다.
설명 hint는 그 수업 기준으로 한 줄.

JSON 배열만 출력한다. 다른 문장은 쓰지 않는다.
형식: [{{"name":"용어","hint":"이 수업에서 한 줄"}}]
"""


def today() -> str:
    return datetime.now(SEOUL).date().isoformat()


def slug(name: str) -> str:
    text = UNSAFE.sub("-", name).strip(" .")
    text = re.sub(r"\s+", "-", text)
    return text[:80] or "수업"


def git_root() -> Path:
    for path in [ROOT, *ROOT.parents]:
        if (path / ".git").exists():
            return path
    raise RuntimeError("git 저장소가 아닙니다.")


def note_paths(lecture: str, day: str) -> tuple[Path, Path]:
    folder = NOTES_DIR / day
    folder.mkdir(parents=True, exist_ok=True)
    stem = slug(lecture)
    return folder / f"{stem}.json", folder / f"{stem}.md"


def parse_entries(payload: dict) -> list[dict]:
    rows = []
    for item in payload.get("entries") or []:
        question = str(item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip()
        if question and answer:
            rows.append({"question": question, "answer": answer})
    return rows


def render_markdown(lecture: str, day: str, entries: list[dict]) -> str:
    lines = [f"# {lecture}", "", f"- 날짜: {day}", ""]
    for item in entries:
        lines.append(f"## {item['question']}")
        lines.append("")
        lines.append(item["answer"].rstrip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def save_notes(lecture: str, entries: list[dict]) -> dict:
    if not lecture:
        raise RuntimeError("수업 주제가 없습니다.")
    if not entries:
        raise RuntimeError("아직 물어본 단어가 없습니다.")
    day = today()
    json_path, md_path = note_paths(lecture, day)
    data = {"lecture": lecture, "date": day, "entries": []}
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"lecture": lecture, "date": day, "entries": []}
    by_q = {
        str(item.get("question") or "").strip(): item
        for item in data.get("entries") or []
        if str(item.get("question") or "").strip()
    }
    for item in entries:
        by_q[item["question"]] = item
    data["lecture"] = lecture
    data["date"] = day
    data["entries"] = list(by_q.values())
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(lecture, day, data["entries"]), encoding="utf-8")
    repo = git_root()
    return {
        "day": day,
        "count": len(data["entries"]),
        "markdown": str(md_path.relative_to(repo)).replace("\\", "/"),
        "json": str(json_path.relative_to(repo)).replace("\\", "/"),
        "files": [json_path, md_path],
    }


def git_publish(files: list[Path], lecture: str, day: str) -> str:
    repo = git_root()
    rels = [str(path.relative_to(repo)).replace("\\", "/") for path in files]
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "형모 양")
    env.setdefault("GIT_AUTHOR_EMAIL", "tytyrrr13@gmail.com")
    env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
    env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "git",
                "-c",
                f"user.name={env['GIT_AUTHOR_NAME']}",
                "-c",
                f"user.email={env['GIT_AUTHOR_EMAIL']}",
                *args,
            ],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

    added = run(["add", "--", *rels])
    if added.returncode != 0:
        raise RuntimeError((added.stderr or added.stdout or "git add 실패").strip())
    status = run(["status", "--porcelain", "--", *rels])
    if not status.stdout.strip():
        return "이미 원격과 같은 내용입니다."
    commit = run(["commit", "-m", f"{day} {lecture} 수업에서 물어본 단어를 남긴다."])
    if commit.returncode != 0:
        raise RuntimeError((commit.stderr or commit.stdout or "git commit 실패").strip())
    push = run(["push", "origin", "HEAD"])
    if push.returncode != 0:
        raise RuntimeError((push.stderr or push.stdout or "git push 실패").strip())
    return "깃에 올렸습니다."


def explain_prompt(payload: dict) -> str:
    lecture = str(payload.get("lecture") or "").strip()
    word = str(payload.get("word") or "").strip()
    question = str(payload.get("question") or word).strip()
    follow = str(payload.get("follow") or "").strip()
    history = payload.get("history") or []
    lines = []
    for item in history[-6:]:
        role = "학생" if item.get("role") == "user" else "조교"
        lines.append(f"{role}: {item.get('text') or ''}")
    transcript = "\n".join(lines) if lines else "(없음)"
    follow_line = {
        "easy": "방금 단어를 더 쉽게, 비유로.",
        "example": "이 수업에서 나올 법한 짧은 예시 하나.",
        "diff": "이 수업에서 자주 헷갈리는 이웃 개념과 차이.",
        "en": "이 수업 슬라이드에 나올 영어 표기와 그 수업에서의 뜻.",
        "exam": "이 수업 시험/실습에서 어떻게 묻히는지.",
    }.get(follow, "새 단어 설명" if not follow else follow)
    return f"""너는 지금 수업의 조교다. 학생이 강의 중에 모르는 단어를 물어본다.

수업 주제: {lecture}

절대 규칙:
- 위키백과/사전 문장을 그대로 옮기지 마라.
- 반드시 '{lecture}' 수업 맥락에서 그 단어가 왜 나오는지부터 설명하라.
- 다른 분야 뜻은, 이 수업 뜻과 헷갈릴 때만 한 줄로 구분하라.
- 한국어. 4~8문장. 필요하면 짧은 목록.
- 마크다운(*, #, 코드펜스)은 쓰지 마라. 강조는 그냥 문장으로.
- 마지막 줄은 '같이 보면: (이 수업의 이웃 개념 하나)'

이번 요청: {follow_line}
단어: {word}
학생 말: {question}

최근 대화:
{transcript}
"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_POST(self) -> None:  # noqa: N802
        path = unquote(self.path.split("?", 1)[0])
        try:
            body = self._read_json()
        except json.JSONDecodeError:
            self._json(400, {"error": "요청을 읽지 못했습니다."})
            return
        try:
            if path == "/api/concepts":
                lecture = str(body.get("lecture") or "").strip()
                if not lecture:
                    self._json(400, {"error": "수업 주제가 없습니다."})
                    return
                items = extract_json(ask_model(concepts_prompt(lecture)))
                clean = []
                for item in items[:10]:
                    name = str(item.get("name") or "").strip()
                    hint = str(item.get("hint") or "").strip()
                    if name:
                        clean.append({"name": name, "hint": hint})
                if not clean:
                    raise RuntimeError("개념을 고르지 못했습니다.")
                self._json(200, {"concepts": clean})
                return
            if path == "/api/explain":
                lecture = str(body.get("lecture") or "").strip()
                word = str(body.get("word") or "").strip()
                if not lecture or not word:
                    self._json(400, {"error": "수업과 단어가 필요합니다."})
                    return
                answer = ask_model(explain_prompt(body))
                self._json(200, {"answer": answer, "word": word})
                return
            if path in ("/api/save", "/api/publish"):
                lecture = str(body.get("lecture") or "").strip()
                saved = save_notes(lecture, parse_entries(body))
                files = saved.pop("files")
                if path == "/api/save":
                    self._json(200, {"ok": True, "message": "노트를 저장했습니다.", **saved})
                    return
                message = git_publish(files, lecture, saved["day"])
                self._json(200, {"ok": True, "message": message, **saved})
                return
            self._json(404, {"error": "없는 주소입니다."})
        except Exception as err:
            self._json(500, {"error": str(err)})


def main() -> None:
    port = int(os.environ.get("PORT") or 8766)
    if not api_key():
        print("CURSOR_API_KEY가 없습니다. lecture-words/.env 또는 daily-english/.env 를 확인하세요.")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"http://127.0.0.1:{port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
