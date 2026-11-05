"""매일 돌아가는 Actions 상태를 status.json으로 남긴다."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "status.json"
SEOUL = ZoneInfo("Asia/Seoul")

JOBS = [
    {
        "id": "daily-english",
        "name": "매일하루영단어",
        "repo": "Hyungmo1234/daily-english",
        "workflow": "daily-short",
        "kind": "slot4h",
        "web": "https://daily-english-hyungmo.fly.dev",
    },
    {
        "id": "daily-english-ja",
        "name": "매일하루영단어 (일본인)",
        "repo": "Hyungmo1234/daily-english",
        "workflow": "daily-ja",
        "kind": "slot4h",
    },
    {
        "id": "daily-nihongo",
        "name": "매일하루일본어",
        "repo": "Hyungmo1234/daily-nihongo",
        "workflow": "daily-short",
        "kind": "slot4h",
    },
    {
        "id": "daily-house",
        "name": "데일리하우스",
        "repo": "Hyungmo1234/daily-house",
        "workflow": "Daily publish",
        "kind": "daily",
        "web": "https://hyungmo1234.github.io/daily-house/",
    },
]

NOISE = re.compile(
    r"^(##\[|\[command\]|Post job|Cleaning up|git version|Temporarily overriding|"
    r"Adding repository|Successfully installed|Downloading |Collecting |Installing |"
    r"Requirement |\[notice\]|shell: |env: |pythonLocation|HTTP Request:)",
    re.I,
)
REASON = re.compile(r"(실패|error|exception|denied|unauthorized|timeout|누락|없습니다)", re.I)


def gh(*args: str, check: bool = True) -> str:
    env = os.environ.copy()
    env.setdefault("GH_PROMPT_DISABLED", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "gh failed").strip()[:400])
    return proc.stdout


def gh_json(*args: str):
    raw = gh(*args)
    raw = raw.strip()
    if not raw:
        return None
    return json.loads(raw)


def to_seoul(iso: str | None) -> datetime | None:
    if not iso:
        return None
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(SEOUL)


def fmt_when(iso: str | None) -> str:
    dt = to_seoul(iso)
    if not dt:
        return ""
    return dt.strftime("%m-%d %H:%M")


def probe_web(url: str) -> dict:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "chkAPJ-status"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return {"ok": 200 <= res.status < 400, "code": res.status}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "code": exc.code, "summary": f"웹 {exc.code}"}
    except Exception as exc:
        msg = str(exc)
        if "getaddrinfo" in msg or "Failed to resolve" in msg or "Name or service" in msg:
            return {"ok": False, "summary": "웹 주소를 찾지 못함"}
        return {"ok": False, "summary": "웹 접속 실패"}


def failed_reason(repo: str, run_id: int) -> str:
    jobs = gh_json("run", "view", str(run_id), "--repo", repo, "--json", "jobs") or {}
    step_name = ""
    for job in jobs.get("jobs") or []:
        for step in job.get("steps") or []:
            if step.get("conclusion") == "failure":
                step_name = step.get("name") or ""
                break
    log = gh("run", "view", str(run_id), "--repo", repo, "--log-failed", check=False)
    picked = ""
    for line in reversed(log.splitlines()):
        text = re.sub(r"^[^\t]*\t[^\t]*\t\d{4}-\d{2}-\d{2}T[^\s]+\s*", "", line).strip()
        text = re.sub(r"^\x1b\[[0-9;]*m", "", text)
        if not text or NOISE.search(text):
            continue
        if text.startswith("##[error]Process completed"):
            continue
        if REASON.search(text) or (text.startswith("##[error]") and "Node.js" not in text):
            picked = re.sub(r"^##\[error\]", "", text).strip()
            break
        if not picked and not text.startswith("##["):
            picked = text
    reason = picked or step_name or "실패 원인을 로그에서 못 읽음"
    return reason[:120]


def house_skipped(repo: str, run_id: int) -> bool:
    data = gh_json("run", "view", str(run_id), "--repo", repo, "--json", "jobs") or {}
    for job in data.get("jobs") or []:
        for step in job.get("steps") or []:
            name = step.get("name") or ""
            if "Skip if today" in name and step.get("conclusion") == "success":
                collect = next(
                    (s for s in (job.get("steps") or []) if "Collect" in (s.get("name") or "")),
                    None,
                )
                if collect and collect.get("conclusion") == "skipped":
                    return True
    return False


def summarize(job: dict, run: dict, now: datetime) -> dict:
    run_id = run["databaseId"]
    repo = job["repo"]
    when = fmt_when(run.get("updatedAt") or run.get("createdAt"))
    url = run.get("url") or ""
    status = run.get("status")
    conclusion = run.get("conclusion")
    created = to_seoul(run.get("createdAt"))
    today = now.date()

    if status in {"queued", "in_progress", "waiting"}:
        return {
            "ok": True,
            "state": "wait",
            "label": "실행 중",
            "summary": f"{when} 돌아가는 중",
            "at": run.get("updatedAt"),
            "url": url,
        }

    if conclusion == "failure":
        return {
            "ok": False,
            "state": "bad",
            "label": "이상",
            "summary": failed_reason(repo, run_id),
            "at": run.get("updatedAt"),
            "url": url,
        }

    if conclusion == "cancelled":
        return {
            "ok": False,
            "state": "bad",
            "label": "이상",
            "summary": f"{when} 실행이 취소됨",
            "at": run.get("updatedAt"),
            "url": url,
        }

    skipped_today = job["kind"] == "daily" and house_skipped(repo, run_id)
    if conclusion == "success":
        summary = f"{when} 성공"
        if skipped_today:
            summary = f"{when} 오늘 치 이미 발행 · 이후 실행은 생략"
        item = {
            "ok": True,
            "state": "ok",
            "label": "정상",
            "summary": summary,
            "at": run.get("updatedAt"),
            "url": url,
        }
        if job["kind"] == "slot4h" and created and now - created > timedelta(hours=7):
            item.update({
                "ok": False,
                "state": "wait",
                "label": "지연",
                "summary": f"마지막 성공 {when} · 이후 슬롯이 안 보임",
            })
        if job["kind"] == "daily" and created and created.date() < today:
            # 어제 성공/생략만 있고 오늘 실행이 없으면 아직 아침 슬롯 대기
            hour = now.hour
            if hour < 23:
                item.update({
                    "ok": True,
                    "state": "wait",
                    "label": "대기",
                    "summary": f"오늘 실행 아직 없음 · 마지막은 {when}",
                })
            else:
                item.update({
                    "ok": False,
                    "state": "bad",
                    "label": "이상",
                    "summary": f"오늘 치가 안 나옴 · 마지막은 {when}",
                })
        return item

    return {
        "ok": False,
        "state": "wait",
        "label": "미확인",
        "summary": f"{when} {conclusion or status or '상태 없음'}",
        "at": run.get("updatedAt"),
        "url": url,
    }


def collect_job(job: dict, now: datetime) -> dict:
    item = {
        "id": job["id"],
        "name": job["name"],
        "ok": False,
        "state": "wait",
        "label": "미확인",
        "summary": "",
        "url": "",
        "at": None,
    }
    try:
        runs = gh_json(
            "run", "list",
            "--repo", job["repo"],
            "--workflow", job["workflow"],
            "--limit", "8",
            "--json", "databaseId,conclusion,status,createdAt,updatedAt,url,event,displayTitle",
        ) or []
    except Exception as exc:
        item["summary"] = str(exc)[:160]
        return item
    if not runs:
        item["summary"] = "실행 기록이 없습니다"
        return item
    item.update(summarize(job, runs[0], now))
    if job.get("web"):
        web = probe_web(job["web"])
        item["web"] = web
        if not web.get("ok"):
            extra = web.get("summary") or f"웹 {web.get('code', '')}".strip()
            if item["ok"]:
                item["ok"] = False
                item["state"] = "bad"
                item["label"] = "이상"
                item["summary"] = extra
            else:
                item["summary"] = f"{item['summary']} · {extra}"
    return item


def main() -> int:
    now = datetime.now(SEOUL)
    jobs = [collect_job(job, now) for job in JOBS]
    bad = [j for j in jobs if not j["ok"]]
    payload = {
        "checkedAt": now.isoformat(timespec="minutes"),
        "ok": not bad,
        "summary": (
            "스케줄 모두 정상"
            if not bad
            else "이상 " + ", ".join(f"{j['name']} ({j['summary']})" for j in bad)
        )[:240],
        "jobs": {j["id"]: j for j in jobs},
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
