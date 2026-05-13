const messages = [
  "保持好心情",
  "今天过得开心嘛",
  "每天都要元气满满",
  "好好爱自己",
  "早安午安晚安",
  "别熬夜",
  "早点休息",
  "顺顺利利",
  "期待下一次见面",
  "想你了",
  "我想你了",
  "愿所有烦恼都消失",
  "梦想成真",
];

const colors = ["#ffd1dc", "#cdeffd", "#d9fdd3", "#ffe7c7", "#efe0ff", "#fff3b0"];

const $ = (id) => document.getElementById(id);

const layer = $("layer");
const btnStart = $("btnStart");
const btnClear = $("btnClear");
const chipStatus = $("chipStatus");

const surveyModal = $("surveyModal");
const surveyForm = $("surveyForm");
const surveyHint = $("surveyHint");
const surveyName = $("surveyName");
const surveyAge = $("surveyAge");
const surveyGender = $("surveyGender");
const surveyCity = $("surveyCity");
const surveyOcc = $("surveyOcc");
const surveyPurpose = $("surveyPurpose");
const surveyFeedback = $("surveyFeedback");
const surveyContact = $("surveyContact");
const surveyConsent = $("surveyConsent");
const surveySubmit = $("surveySubmit");

const inputCountHeart = $("countHeart");
const inputCountRandom = $("countRandom");
const inputIntervalMs = $("intervalMs");
const inputTtlMs = $("ttlMs");

const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

const storageKey = "lovePopSurveySubmittedV1";
let surveyReady = false;

const setButtonsEnabled = (enabled) => {
  btnStart.disabled = !enabled;
  btnClear.disabled = !enabled;
  btnStart.style.opacity = enabled ? "1" : "0.65";
  btnClear.style.opacity = enabled ? "1" : "0.65";
};

const showSurvey = () => {
  if (!surveyModal) return;
  surveyModal.hidden = false;
  surveyHint.textContent = "";
  setButtonsEnabled(false);
  chipStatus.textContent = "请先填写信息";
  window.setTimeout(() => {
    try {
      surveyName.focus();
    } catch {}
  }, 0);
};

const hideSurvey = () => {
  if (!surveyModal) return;
  surveyModal.hidden = true;
  setButtonsEnabled(true);
  chipStatus.textContent = "就绪";
};

const submitSurvey = async () => {
  const payload = {
    name: surveyName.value.trim(),
    ageRange: surveyAge.value,
    gender: surveyGender.value,
    city: surveyCity.value.trim(),
    occupation: surveyOcc.value.trim(),
    purpose: surveyPurpose.value,
    feedback: surveyFeedback.value.trim(),
    contact: surveyContact.value.trim(),
    consent: surveyConsent.checked,
  };

  if (!payload.name) {
    surveyHint.textContent = "请填写昵称";
    return false;
  }
  if (!payload.ageRange || !payload.gender) {
    surveyHint.textContent = "请选择年龄段与性别";
    return false;
  }
  if (!payload.consent) {
    surveyHint.textContent = "需要勾选同意才能提交";
    return false;
  }

  surveyHint.textContent = "提交中…";
  surveySubmit.disabled = true;
  try {
    const res = await fetch("/api/survey", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      surveyHint.textContent = "提交失败，请稍后再试";
      return false;
    }
    localStorage.setItem(storageKey, "1");
    surveyReady = true;
    hideSurvey();
    return true;
  } catch {
    surveyHint.textContent = "无法连接后端，请先启动后端服务";
    return false;
  } finally {
    surveySubmit.disabled = false;
  }
};

const heartXY = (t) => {
  const x = 16 * Math.pow(Math.sin(t), 3);
  const y =
    13 * Math.cos(t) -
    5 * Math.cos(2 * t) -
    2 * Math.cos(3 * t) -
    Math.cos(4 * t);
  return { x, y };
};

const computeHeartPositions = (viewportW, viewportH, cardW, cardH, count, margin = 18) => {
  const usableW = Math.max(1, viewportW - margin * 2);
  const usableH = Math.max(1, viewportH - margin * 2);
  const cx = margin + usableW / 2;
  const cy = margin + usableH / 2;
  let scale = Math.min(usableW / (32 + 6), usableH / (30 + 6));
  scale *= 0.95;

  const positions = [];
  for (let i = 0; i < count; i += 1) {
    const t = (i / Math.max(1, count)) * (Math.PI * 2) + (Math.random() * 0.07 - 0.035);
    const { x, y } = heartXY(t);
    let px = Math.round(cx + x * scale + (Math.random() * 21 - 10));
    let py = Math.round(cy - y * scale + (Math.random() * 21 - 10));
    px = clamp(px, 0, viewportW - cardW);
    py = clamp(py, 0, viewportH - cardH);
    positions.push([px, py]);
  }
  return positions;
};

class Engine {
  constructor() {
    this.running = false;
    this.phase = "heart";
    this.spawned = 0;
    this.heartPositions = [];
    this.timer = null;
    this.popups = new Set();
  }

  readConfig() {
    const countHeart = clamp(parseInt(inputCountHeart.value, 10) || 180, 1, 600);
    const countRandom = clamp(parseInt(inputCountRandom.value, 10) || 160, 0, 600);
    const intervalMs = clamp(parseInt(inputIntervalMs.value, 10) || 25, 10, 200);
    const ttlMs = clamp(parseInt(inputTtlMs.value, 10) || 0, 0, 20000);
    return { countHeart, countRandom, intervalMs, ttlMs };
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.phase = "heart";
    this.spawned = 0;

    const { countHeart } = this.readConfig();
    const { w, h } = this.viewport();
    const { cardW, cardH } = this.cardSize();
    this.heartPositions = computeHeartPositions(w, h, cardW, cardH, countHeart);
    chipStatus.textContent = "播放中";
    btnStart.textContent = "暂停";
    this.schedule();
  }

  stop({ clear = false } = {}) {
    this.running = false;
    if (this.timer) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
    btnStart.textContent = "开始";
    chipStatus.textContent = clear ? "已清空" : "已暂停";
    if (clear) this.clear();
  }

  toggle() {
    if (!surveyReady) {
      showSurvey();
      return;
    }
    if (this.running) this.stop();
    else this.start();
  }

  clear() {
    for (const p of Array.from(this.popups)) p.dismiss(true);
    this.popups.clear();
    layer.innerHTML = "";
  }

  viewport() {
    return { w: window.innerWidth, h: window.innerHeight };
  }

  cardSize() {
    return { cardW: 240, cardH: 70 };
  }

  schedule() {
    const { intervalMs } = this.readConfig();
    this.timer = window.setTimeout(() => this.tick(), intervalMs);
  }

  tick() {
    if (!this.running) return;
    const { countHeart, countRandom } = this.readConfig();
    const { w, h } = this.viewport();
    const { cardW, cardH } = this.cardSize();

    let x = 0;
    let y = 0;

    if (this.phase === "heart") {
      if (this.spawned >= countHeart) {
        this.phase = "random";
        this.spawned = 0;
        this.schedule();
        return;
      }
      const pos = this.heartPositions[this.spawned] || [
        Math.floor(Math.random() * (w - cardW)),
        Math.floor(Math.random() * (h - cardH)),
      ];
      x = pos[0];
      y = pos[1];
    } else {
      if (this.spawned >= countRandom) {
        this.running = false;
        btnStart.textContent = "开始";
        chipStatus.textContent = "完成";
        return;
      }
      x = Math.floor(Math.random() * Math.max(1, w - cardW));
      y = Math.floor(Math.random() * Math.max(1, h - cardH));
    }

    const p = new Popup({
      x,
      y,
      w: cardW,
      h: cardH,
      message: pick(messages),
      bg: pick(colors),
      showHint: this.phase === "heart" && this.spawned === 0,
      ttlMs: this.readConfig().ttlMs,
      onDismiss: () => this.popups.delete(p),
    });
    this.popups.add(p);
    p.mount(layer);

    this.spawned += 1;
    this.schedule();
  }
}

class Popup {
  constructor({ x, y, w, h, message, bg, showHint, ttlMs, onDismiss }) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
    this.message = message;
    this.bg = bg;
    this.showHint = showHint;
    this.ttlMs = ttlMs;
    this.onDismiss = onDismiss;
    this.el = null;
    this.ttlTimer = null;
  }

  mount(parent) {
    const el = document.createElement("div");
    el.className = "popup";
    el.style.setProperty("--x", `${this.x}px`);
    el.style.setProperty("--y", `${this.y}px`);
    el.style.setProperty("--w", `${this.w}px`);
    el.style.setProperty("--h", `${this.h}px`);
    el.style.setProperty("--bg", this.bg);

    const hint = this.showHint ? "按 ESC 停止并清空" : "";

    el.innerHTML = `
      <div class="popupCard" role="group" aria-label="弹窗">
        <div class="popupGlass"></div>
        <div class="popupHeader">
          <span class="heart">❤</span>
          <span>${hint}</span>
        </div>
        <button class="popupClose" type="button" aria-label="关闭">×</button>
        <div class="popupText">${escapeHtml(this.message)}</div>
      </div>
    `;

    const closeBtn = el.querySelector(".popupClose");
    closeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.dismiss();
    });

    el.addEventListener("click", () => this.dismiss());
    parent.appendChild(el);
    this.el = el;

    if (this.ttlMs && this.ttlMs > 0) {
      this.ttlTimer = window.setTimeout(() => this.dismiss(), this.ttlMs);
    }
  }

  dismiss(immediate = false) {
    if (!this.el) return;
    if (this.ttlTimer) {
      window.clearTimeout(this.ttlTimer);
      this.ttlTimer = null;
    }

    const el = this.el;
    this.el = null;

    const done = () => {
      el.removeEventListener("animationend", done);
      el.remove();
      if (this.onDismiss) this.onDismiss();
    };

    if (immediate) {
      done();
      return;
    }

    el.addEventListener("animationend", done);
    el.classList.add("popupOut");
  }
}

const escapeHtml = (s) =>
  String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const engine = new Engine();

btnStart.addEventListener("click", () => engine.toggle());
btnClear.addEventListener("click", () => engine.stop({ clear: true }));

window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") engine.stop({ clear: true });
});

window.addEventListener("resize", () => {
  if (!engine.running) return;
  const { countHeart } = engine.readConfig();
  const { w, h } = engine.viewport();
  const { cardW, cardH } = engine.cardSize();
  engine.heartPositions = computeHeartPositions(w, h, cardW, cardH, countHeart);
});

chipStatus.textContent = "就绪";

if (surveyForm) {
  surveyForm.addEventListener("submit", (e) => {
    e.preventDefault();
    submitSurvey();
  });
}

surveyReady = localStorage.getItem(storageKey) === "1";
if (!surveyReady) {
  showSurvey();
} else {
  hideSurvey();
}
