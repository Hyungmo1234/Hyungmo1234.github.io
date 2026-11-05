const RECENT_KEY = "lecture-words.recent";
const FOLLOW_UP = [
  ["더쉽게", "쉽게", "쉽게설명", "초등", "쉬운말"],
  ["예제", "예시", "예문", "코드"],
  ["차이", "비교", "vs", "다른점"],
  ["영어", "영문", "english"],
  ["시험", "출제", "정리"]
];

const $ = (id) => document.getElementById(id);
const setup = $("setup");
const classroom = $("classroom");
const classInput = $("class-input");
const lectureTitle = $("lecture-title");
const conceptGrid = $("concept-grid");
const logEl = $("log");
const askInput = $("ask-input");
const saveStatus = $("save-status");
const publishBtn = $("publish");

const state = {
  lecture: "",
  lastWord: "",
  history: [],
  entries: [],
  busy: false
};

function loadRecent() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]").slice(0, 6);
  } catch {
    return [];
  }
}

function saveRecent(name) {
  const next = [name, ...loadRecent().filter((x) => x !== name)].slice(0, 6);
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
}

function renderRecent() {
  const items = loadRecent();
  const box = $("recent");
  const list = $("recent-list");
  if (!items.length) {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  list.innerHTML = "";
  for (const name of items) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = name;
    btn.addEventListener("click", () => enterClass(name));
    list.append(btn);
  }
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function formatBot(text) {
  return esc(text).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
}

function addBubble(role, text, word = "") {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  const body = role === "bot" ? formatBot(text) : esc(text);
  div.innerHTML = `${word ? `<span class="word">${esc(word)}</span>` : ""}${body}`;
  logEl.append(div);
  logEl.scrollTop = logEl.scrollHeight;
  return div;
}

function detectFollowUp(raw) {
  const compact = raw.replace(/\s+/g, "").toLowerCase();
  if (!state.lastWord) return "";
  if (FOLLOW_UP[0].some((k) => compact.includes(k))) return "easy";
  if (FOLLOW_UP[1].some((k) => compact.includes(k))) return "example";
  if (FOLLOW_UP[2].some((k) => compact.includes(k))) return "diff";
  if (FOLLOW_UP[3].some((k) => compact.includes(k))) return "en";
  if (FOLLOW_UP[4].some((k) => compact.includes(k))) return "exam";
  if (compact.length <= 8 && /^(왜|어떻게|그래서|그게|그럼)/.test(raw)) return "easy";
  return "";
}

function pickWord(raw) {
  return raw
    .replace(/^(이게|그게|단어|용어)?\s*/, "")
    .replace(/\s*(이|가|은|는|을|를)?\s*(뭐야|뭐예요|뭔가요|무엇인가요|알려줘|설명해|뜻)[?.!]*$/u, "")
    .replace(/[?.!]/g, "")
    .trim();
}

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.error || `요청 실패 (${res.status})`;
    if (res.status === 404) {
      throw new Error("모델 서버가 아닙니다. lecture-words 폴더에서 python server.py 를 실행하세요.");
    }
    throw new Error(msg);
  }
  return data;
}

function renderConcepts(items) {
  conceptGrid.innerHTML = "";
  if (!items.length) {
    conceptGrid.innerHTML = '<p class="soft">개념을 고르지 못했습니다. 아래 칸에 단어를 바로 물어보세요.</p>';
    return;
  }
  for (const item of items) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "concept";
    btn.innerHTML = `<b>${esc(item.name)}</b><span>${esc(item.hint || "")}</span>`;
    btn.addEventListener("click", () => askWord(item.name));
    conceptGrid.append(btn);
  }
}

async function loadConcepts(lecture) {
  try {
    const data = await api("/api/concepts", { lecture });
    renderConcepts(data.concepts || []);
  } catch (err) {
    conceptGrid.innerHTML = `<p class="soft">${esc(err.message)}</p>`;
  }
}

async function enterClass(name) {
  const lecture = name.trim();
  if (!lecture) return;
  state.lecture = lecture;
  state.lastWord = "";
  state.history = [];
  state.entries = [];
  if (saveStatus) saveStatus.textContent = "물어본 단어를 노트에 모아 깃에 올립니다.";
  saveRecent(lecture);
  renderRecent();
  setup.hidden = true;
  classroom.hidden = false;
  lectureTitle.textContent = lecture;
  logEl.innerHTML = "";
  addBubble("bot", `지금은 ${lecture} 수업입니다.\n\n모르는 단어가 무엇인가요? 개념을 눌러도 되고, 아래에 바로 적어도 됩니다.`);
  conceptGrid.innerHTML = '<p class="soft">이 수업에서 나올 개념을 고르는 중…</p>';
  askInput.focus();
  await loadConcepts(lecture);
}

async function askWord(raw) {
  const text = raw.trim();
  if (!text || state.busy) return;
  addBubble("user", text);
  askInput.value = "";
  const follow = detectFollowUp(text);
  const word = follow ? state.lastWord : pickWord(text) || text;
  state.history.push({ role: "user", text });
  state.busy = true;
  const pending = addBubble("bot", "이 수업 기준으로 설명하는 중…", follow ? "이어서" : word);
  try {
    const data = await api("/api/explain", {
      lecture: state.lecture,
      word,
      question: text,
      follow,
      history: state.history
    });
    const answer = data.answer || "";
    state.lastWord = word;
    state.history.push({ role: "bot", text: answer });
    state.entries.push({ question: text, answer });
    pending.remove();
    addBubble("bot", answer, follow ? `${word} · 이어서` : word);
    api("/api/save", { lecture: state.lecture, entries: state.entries }).then((saved) => {
      if (saveStatus) saveStatus.textContent = `로컬 노트 ${saved.count}개 · ${saved.markdown}`;
    }).catch(() => {});
  } catch (err) {
    pending.remove();
    addBubble("bot", err.message, word);
  } finally {
    state.busy = false;
    askInput.focus();
  }
}

$("class-form").addEventListener("submit", (e) => {
  e.preventDefault();
  enterClass(classInput.value);
});
$("ask-form").addEventListener("submit", (e) => {
  e.preventDefault();
  askWord(askInput.value);
});
$("change-class").addEventListener("click", () => {
  classroom.hidden = true;
  setup.hidden = false;
  classInput.focus();
  classInput.select();
});
publishBtn.addEventListener("click", async () => {
  if (state.busy) return;
  if (!state.entries.length) {
    saveStatus.textContent = "아직 물어본 단어가 없습니다.";
    return;
  }
  state.busy = true;
  publishBtn.disabled = true;
  saveStatus.textContent = "노트를 깃에 올리는 중…";
  try {
    const data = await api("/api/publish", {
      lecture: state.lecture,
      entries: state.entries
    });
    saveStatus.textContent = `${data.message} (${data.markdown})`;
  } catch (err) {
    saveStatus.textContent = err.message;
  } finally {
    state.busy = false;
    publishBtn.disabled = false;
    askInput.focus();
  }
});

renderRecent();
classInput.focus();
