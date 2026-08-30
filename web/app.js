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
const settingsPanel = $("settingsPanel");
const togglePanel = $("togglePanel");

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
const selectShape = $("shapeType");
const inputSizeScale = $("sizeScale");
const inputCustomMessages = $("customMessages");

const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

const storageKey = "lovePopSurveySubmittedV1";
let surveyReady = false;
const apiBase = String(window.__LOVEPOP_API_BASE__ || "").replace(/\/+$/, "");
let panelCollapsed = false;

const setPanelCollapsed = (collapsed) => {
  if (!settingsPanel) return;
  panelCollapsed = collapsed;
  settingsPanel.classList.toggle("collapsed", collapsed);
};

if (togglePanel && settingsPanel) {
  togglePanel.addEventListener("click", () => setPanelCollapsed(!panelCollapsed));
}

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
    const url = apiBase ? `${apiBase}/api/survey` : "/api/survey";
    const res = await fetch(url, {
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

const getPolygonPoints = (verts, count) => {
  let totalLen = 0;
  const edges = [];
  for (let i = 0; i < verts.length; i++) {
    const p1 = verts[i];
    const p2 = verts[(i + 1) % verts.length];
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const len = Math.sqrt(dx * dx + dy * dy);
    edges.push({ p1, p2, len, dx, dy });
    totalLen += len;
  }
  const positions = [];
  let currentEdge = 0;
  let currentDist = 0;
  for (let i = 0; i < count; i++) {
    const targetDist = (i / count) * totalLen;
    while (currentEdge < edges.length - 1 && targetDist > currentDist + edges[currentEdge].len) {
      currentDist += edges[currentEdge].len;
      currentEdge++;
    }
    const edge = edges[currentEdge];
    const t = edge.len === 0 ? 0 : (targetDist - currentDist) / edge.len;
    positions.push({ x: edge.p1.x + edge.dx * t, y: edge.p1.y + edge.dy * t });
  }
  return positions;
};

const generateShape = (type, count) => {
  if (type === 'heart') {
    const positions = [];
    for (let i = 0; i < count; i++) {
      const t = (i / Math.max(1, count)) * (Math.PI * 2) + (Math.random() * 0.07 - 0.035);
      positions.push(heartXY(t));
    }
    return positions;
  } else if (type === 'star5') {
    const verts = [];
    for(let i=0; i<10; i++) {
      const r = i % 2 === 0 ? 16 : 6.1;
      const angle = (i * Math.PI) / 5 + Math.PI / 2;
      verts.push({ x: r * Math.cos(angle), y: r * Math.sin(angle) });
    }
    return getPolygonPoints(verts, count);
  } else if (type === 'star6') {
    const verts = [];
    for(let i=0; i<12; i++) {
      const r = i % 2 === 0 ? 16 : 9.2;
      const angle = (i * Math.PI) / 6 + Math.PI / 2;
      verts.push({ x: r * Math.cos(angle), y: r * Math.sin(angle) });
    }
    return getPolygonPoints(verts, count);
  }
  return [];
};

const computePositions = (viewportW, viewportH, cardW, cardH, count, shapeType, sizeScale, margin = 18) => {
  const usableW = Math.max(1, viewportW - margin * 2);
  const usableH = Math.max(1, viewportH - margin * 2);
  const cx = margin + usableW / 2;
  const cy = Math.max(margin, (viewportH - 160) / 2); 
  let scale = Math.min(usableW / 38, usableH / 36) * 0.95 * sizeScale;

  const basePoints = generateShape(shapeType, count);
  const positions = [];
  for (let i = 0; i < count; i++) {
    const bp = basePoints[i];
    let px = Math.round(cx + bp.x * scale + (Math.random() * 21 - 10));
    let py = Math.round(cy - bp.y * scale + (Math.random() * 21 - 10));
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
    const shapeType = selectShape.value || "heart";
    const sizeScale = clamp(parseFloat(inputSizeScale.value) || 1.0, 0.5, 3.0);
    
    let activeMessages = messages;
    const customText = inputCustomMessages.value.trim();
    if (customText) {
      activeMessages = customText.split('\n').map(s => s.trim()).filter(Boolean);
      if (activeMessages.length === 0) activeMessages = messages;
    }

    return { countHeart, countRandom, intervalMs, ttlMs, shapeType, sizeScale, activeMessages };
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.phase = "heart";
    this.spawned = 0;
    setPanelCollapsed(true);

    const config = this.readConfig();
    this.currentConfig = config;
    
    const { w, h } = this.viewport();
    const { cardW, cardH } = this.cardSize();
    this.heartPositions = computePositions(w, h, cardW, cardH, config.countHeart, config.shapeType, config.sizeScale);
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
    setPanelCollapsed(false);
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
    if (!this.running) return;
    const { intervalMs } = this.currentConfig;
    this.timer = window.setTimeout(() => this.tick(), intervalMs);
  }

  tick() {
    if (!this.running) return;
    const { countHeart, countRandom, ttlMs, activeMessages } = this.currentConfig;
    const { w, h } = this.viewport();
    const { cardW, cardH } = this.cardSize();

    let px, py;
    if (this.phase === "heart") {
      if (this.spawned >= countHeart) {
        this.phase = "random";
        this.spawned = 0;
        this.schedule();
        return;
      }
      [px, py] = this.heartPositions[this.spawned];
    } else {
      if (this.spawned >= countRandom) {
        this.phase = "done";
        this.stop();
        return;
      }
      px = Math.round(Math.random() * Math.max(0, w - cardW));
      py = Math.round(Math.random() * Math.max(0, h - cardH));
    }

    const p = new Popup({
      parent: layer,
      x: px,
      y: py,
      w: cardW,
      h: cardH,
      message: pick(activeMessages),
      bg: pick(colors),
      showHint: this.phase === "heart" && this.spawned === 0,
      ttlMs: ttlMs,
      onDismiss: () => this.popups.delete(p),
    });

    this.popups.add(p);
    this.spawned += 1;
    this.schedule();
  }
}

class Popup {
  constructor({ parent, x, y, w, h, message, bg, showHint, ttlMs, onDismiss }) {
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

    this.el.getBoundingClientRect(); // reflow
    this.el.style.transform = `translate3d(${this.x}px, ${this.y}px, 0)`;

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

// ======= 评价区功能 =======
const btnReview = $("btnReview");
const reviewsModal = $("reviewsModal");
const closeReviews = $("closeReviews");
const reviewsList = $("reviewsList");
const reviewForm = $("reviewForm");
const starRating = $("starRating");
const reviewScore = $("reviewScore");
const reviewHint = $("reviewHint");
const reviewSubmit = $("reviewSubmit");

const renderReviews = (data) => {
  if (!data || data.length === 0) {
    reviewsList.innerHTML = `<div style="text-align:center; padding: 20px; color: gray;">暂时没有评价，快来抢沙发！</div>`;
    return;
  }
  reviewsList.innerHTML = data.map(r => `
    <div class="reviewItem">
      <div class="reviewItemHead">
        <div class="reviewItemName">${r.name}</div>
        <div class="reviewItemDate">${new Date(r.created_at + "Z").toLocaleString()}</div>
      </div>
      <div class="reviewItemScore">${"★".repeat(r.score)}${"☆".repeat(5 - r.score)}</div>
      <div class="reviewItemBody">${r.comment}</div>
    </div>
  `).join("");
};

const fetchReviews = async () => {
  reviewsList.innerHTML = `<div style="text-align:center; padding: 20px; color: gray;">加载中...</div>`;
  try {
    const url = apiBase ? `${apiBase}/api/reviews` : "/api/reviews";
    const res = await fetch(url);
    const json = await res.json();
    if (json.ok) renderReviews(json.data);
  } catch (e) {
    reviewsList.innerHTML = `<div style="text-align:center; padding: 20px; color: gray;">加载失败</div>`;
  }
};

btnReview.onclick = () => {
  reviewsModal.hidden = false;
  fetchReviews();
};

closeReviews.onclick = () => {
  reviewsModal.hidden = true;
};

// 星星打分交互
const stars = starRating.querySelectorAll("span");
stars.forEach(star => {
  star.onclick = () => {
    const val = parseInt(star.getAttribute("data-val"), 10);
    reviewScore.value = val;
    stars.forEach(s => {
      const v = parseInt(s.getAttribute("data-val"), 10);
      s.className = v <= val ? "active" : "";
    });
  };
  star.onmouseenter = () => {
    const val = parseInt(star.getAttribute("data-val"), 10);
    stars.forEach(s => {
      const v = parseInt(s.getAttribute("data-val"), 10);
      if (v <= val) s.classList.add("hover");
    });
  };
  star.onmouseleave = () => {
    stars.forEach(s => s.classList.remove("hover"));
  };
});

reviewForm.onsubmit = async (e) => {
  e.preventDefault();
  const name = $("reviewName").value.trim();
  const comment = $("reviewComment").value.trim();
  const score = parseInt(reviewScore.value, 10);

  if (!comment) return;

  reviewSubmit.disabled = true;
  reviewHint.textContent = "提交中...";
  
  try {
    const url = apiBase ? `${apiBase}/api/reviews` : "/api/reviews";
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, score, comment })
    });
    const json = await res.json();
    if (json.ok) {
      reviewHint.textContent = "提交成功！";
      $("reviewComment").value = "";
      setTimeout(() => { reviewHint.textContent = ""; }, 2000);
      fetchReviews();
    } else {
      reviewHint.textContent = "提交失败: " + json.error;
    }
  } catch (err) {
    reviewHint.textContent = "网络错误，请稍后再试";
  } finally {
    reviewSubmit.disabled = false;
  }
};

const engine = new Engine();

btnStart.addEventListener("click", () => {
  if (!surveyReady) {
    showSurvey();
    return;
  }
  engine.toggle();
});
btnClear.addEventListener("click", () => engine.stop({ clear: true }));

window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") engine.stop({ clear: true });
});

window.addEventListener("resize", () => {
  if (!engine.running) return;
  const config = engine.readConfig();
  const { w, h } = engine.viewport();
  const { cardW, cardH } = engine.cardSize();
  engine.heartPositions = computePositions(w, h, cardW, cardH, config.countHeart, config.shapeType, config.sizeScale);
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
