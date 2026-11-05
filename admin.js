const ADMIN_REPO = "Hyungmo1234/Hyungmo1234.github.io";
const ADMIN_BRANCH = "main";
const PBKDF2_ITERS = 210000;

const admin = {
  config: null,
  token: null
};

function b64ToBytes(b64) {
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) out[i] = bin.charCodeAt(i);
  return out;
}

function bytesToB64(bytes) {
  let bin = "";
  bytes.forEach((b) => { bin += String.fromCharCode(b); });
  return btoa(bin);
}

function strToB64(str) {
  return bytesToB64(new TextEncoder().encode(str));
}

function b64ToStr(b64) {
  return new TextDecoder().decode(b64ToBytes(b64));
}

async function deriveKey(password, salt) {
  const material = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ITERS, hash: "SHA-256" },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

async function encryptSecret(password, payload) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(password, salt);
  const cipher = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    new TextEncoder().encode(JSON.stringify(payload))
  );
  return {
    repo: ADMIN_REPO,
    salt: bytesToB64(salt),
    iv: bytesToB64(iv),
    data: bytesToB64(new Uint8Array(cipher))
  };
}

async function decryptSecret(password, config) {
  const key = await deriveKey(password, b64ToBytes(config.salt));
  const plain = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: b64ToBytes(config.iv) },
    key,
    b64ToBytes(config.data)
  );
  return JSON.parse(new TextDecoder().decode(plain));
}

async function loadAdminConfig() {
  if (admin.config) return admin.config;
  const res = await fetch("admin.config.json", { cache: "no-store" });
  if (!res.ok) return null;
  admin.config = await res.json();
  return admin.config;
}

async function unlockAdmin(password) {
  if (admin.token) return admin.token;
  const config = await loadAdminConfig();
  if (!config || !config.data) {
    throw new Error("관리자 설정 파일이 없습니다. admin-setup.html에서 비밀번호와 토큰을 먼저 만드세요.");
  }
  try {
    const payload = await decryptSecret(password, config);
    if (!payload || !payload.token) throw new Error("empty");
    admin.token = payload.token;
    return admin.token;
  } catch (err) {
    if (err && err.message && err.message.includes("관리자 설정")) throw err;
    throw new Error("비밀번호가 다릅니다.");
  }
}

async function ghJson(path, options) {
  const res = await fetch("https://api.github.com" + path, {
    ...options,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: "Bearer " + admin.token,
      "X-GitHub-Api-Version": "2022-11-28",
      ...(options && options.headers)
    }
  });
  const text = await res.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch (_) { body = { message: text }; }
  if (!res.ok) {
    throw new Error((body && body.message) || ("GitHub " + res.status));
  }
  return body;
}

async function putFile(path, content, message) {
  let sha;
  try {
    const current = await ghJson(
      `/repos/${ADMIN_REPO}/contents/${encodeURIComponent(path).replace(/%2F/g, "/")}?ref=${ADMIN_BRANCH}`
    );
    sha = current.sha;
  } catch (_) { /* 새 파일 */ }
  const body = {
    message,
    content: strToB64(content),
    branch: ADMIN_BRANCH
  };
  if (sha) body.sha = sha;
  return ghJson(`/repos/${ADMIN_REPO}/contents/${encodeURIComponent(path).replace(/%2F/g, "/")}`, {
    method: "PUT",
    body: JSON.stringify(body)
  });
}

function stamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}`;
}

async function saveProjectEdit(projectId, fields) {
  const file = await ghJson(`/repos/${ADMIN_REPO}/contents/projects.json?ref=${ADMIN_BRANCH}`);
  const catalog = JSON.parse(b64ToStr(file.content.replace(/\n/g, "")));
  const item = (catalog.projects || []).find((p) => p.id === projectId);
  if (!item) throw new Error("프로젝트 항목을 찾지 못했습니다.");
  item.name = fields.name;
  item.blurb = fields.blurb;
  item.note = fields.note;
  if (!item.note) delete item.note;
  await ghJson(`/repos/${ADMIN_REPO}/contents/projects.json`, {
    method: "PUT",
    body: JSON.stringify({
      message: `${item.name} 카드 문구를 고친다.`,
      content: strToB64(JSON.stringify(catalog, null, 2) + "\n"),
      branch: ADMIN_BRANCH,
      sha: file.sha
    })
  });
}

async function saveWish(project, wish, statusLine) {
  const when = new Date().toISOString();
  const slug = (project && project.id) || "site";
  const title = (project && project.name) || "사이트";
  const lines = [
    `# ${title}`,
    "",
    `- 시각: ${when}`,
    `- 프로젝트: ${title}`
  ];
  if (statusLine) lines.push(`- 당시 상태: ${statusLine}`);
  lines.push("", "## 이렇게 고쳤으면", "", wish.trim(), "");
  const path = `inbox/${stamp()}-${slug}.md`;
  await putFile(path, lines.join("\n"), `${title} 수정 요청을 남긴다.`);
  return path;
}

window.HMAdmin = {
  encryptSecret,
  decryptSecret,
  loadAdminConfig,
  unlockAdmin,
  saveProjectEdit,
  saveWish
};
