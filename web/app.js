const messages = [
  "保持好心情",
  "今天也要闪闪发光",
  "好好爱自己",
  "愿所有烦恼都消失",
  "顺顺利利",
  "早点休息",
  "梦想成真",
  "期待下一次见面",
  "你值得被认真对待",
  "把快乐收藏起来",
];

const palettes = {
  gentle: ["#fff0f4", "#eef6ff", "#f3fff8", "#fff8e8", "#f6f0ff"],
  bright: ["#ffe9a8", "#dff9ef", "#dcecff", "#ffe4ee", "#eaf7d7"],
  star: ["#f2f4ff", "#fff3c4", "#e8fbff", "#fce7f3", "#ecfdf5"],
};

const presetConfig = {
  gentle: {
    shapeType: "heart",
    sizeScale: 1,
    countHeart: 150,
    countRandom: 70,
    intervalMs: 24,
    ttlMs: 0,
    messages: "保持好心情\n愿你被温柔以待\n今天也要闪闪发光",
  },
  bright: {
    shapeType: "heart",
    sizeScale: 1.15,
    countHeart: 180,
    countRandom: 120,
    intervalMs: 18,
    ttlMs: 6500,
    messages: "元气满满\n顺顺利利\n好运正在靠近",
  },
  star: {
    shapeType: "star5",
    sizeScale: 1.1,
    countHeart: 170,
    countRandom: 60,
    intervalMs: 22,
    ttlMs: 8500,
    messages: "星光不问赶路人\n愿望会慢慢实现\n今晚也很适合浪漫",
  },
};

const $ = (id) => document.getElementById(id);
const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

const layer = $("layer");
const emptyState = $("emptyState");
const btnStart = $("btnStart");
const btnHeroStart = $("btnHeroStart");
const btnDemo = $("btnDemo");
const btnClear = $("btnClear");
const btnReset = $("btnReset");
const btnScreenshot = $("btnScreenshot");
const chipStatus = $("chipStatus");
const metricCreated = $("metricCreated");
const metricVisible = $("metricVisible");
const metricMode = $("metricMode");
const progressBar = $("progressBar");

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

const btnReview = $("btnReview");
const reviewsModal = $("reviewsModal");
const closeReviews = $("closeReviews");
const reviewsList = $("reviewsList");
const reviewForm = $("reviewForm");
const starRating = $("starRating");
const reviewScore = $("reviewScore");
const reviewHint = $("reviewHint");
const reviewSubmit = $("reviewSubmit");

const storageKey = "lovePopSurveySubmittedV2";
const apiBase = String(window.__LOVEPOP_API_BASE__ || "").replace(/\/+$/, "");
let surveyReady = localStorage.getItem(storageKey) === "1";
let activePreset = "gentle";

const shapeLabel = (type) => ({ heart: "爱心", star5: "五角星", star6: "六芒星" }[type] || "爱心");

const escapeHtml = (s) =>
  String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const setButtonsEnabled = (enabled) => {
  [btnStart, btnHeroStart, btnDemo, btnClear].filter(Boolean).forEach((btn) => {
    btn.disabled = !enabled;
    btn.style.opacity = enabled ? "1" : "0.62";
  });
};

const updateMetrics = ({ status, created, visible, progress, mode } = {}) => {
  if (status) chipStatus.textContent = status;
  if (typeof created === "number") metricCreated.textContent = String(created);
  if (typeof visible === "number") metricVisible.textContent = String(visible);
  if (typeof progress === "number") progressBar.style.width = `${clamp(progress, 0, 100)}%`;
  if (mode) metricMode.textContent = shapeLabel(mode);
};

const showSurvey = () => {
  surveyModal.hidden = false;
  surveyHint.textContent = "";
  setButtonsEnabled(false);
  updateMetrics({ status: "待填写" });
  window.setTimeout(() => surveyName.focus(), 0);
};

const hideSurvey = () => {
  surveyModal.hidden = true;
  setButtonsEnabled(true);
  updateMetrics({ status: "就绪" });
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

  surveyHint.textContent = "提交中...";
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
    surveyHint.textContent = "暂时无法连接后端，请稍后再试";
    return false;
  } finally {
    surveySubmit.disabled = false;
  }
};

const heartXY = (t) => {
  const x = 16 * Math.pow(Math.sin(t), 3);
  const y = 13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t);
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
    edges.push({ p1, len, dx, dy });
    totalLen += len;
  }

  const positions = [];
  let currentEdge = 0;
  let currentDist = 0;
  for (let i = 0; i < count; i++) {
    const targetDist = (i / Math.max(1, count)) * totalLen;
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
  if (type === "heart") {
    return Array.from({ length: count }, (_, i) => {
      const t = (i / Math.max(1, count)) * Math.PI * 2 + (Math.random() * 0.07 - 0.035);
      return heartXY(t);
    });
  }

  const points = type === "star6" ? 12 : 10;
  const outer = 16;
  const inner = type === "star6" ? 9.2 : 6.1;
  const verts = Array.from({ length: points }, (_, i) => {
    const r = i % 2 === 0 ? outer : inner;
    const angle = (i * Math.PI) / (points / 2) + Math.PI / 2;
    return { x: r * Math.cos(angle), y: r * Math.sin(angle) };
  });
  return getPolygonPoints(verts, count);
};

const computePositions = (viewportW, viewportH, cardW, cardH, count, shapeType, sizeScale, margin = 18) => {
  const usableW = Math.max(1, viewportW - margin * 2);
  const usableH = Math.max(1, viewportH - margin * 2);
  const cx = margin + usableW / 2;
  const cy = margin + usableH / 2 + 18;
  const scale = Math.min(usableW / 40, usableH / 36) * 0.86 * sizeScale;

  return generateShape(shapeType, count).map((bp) => {
    let px = Math.round(cx + bp.x * scale + (Math.random() * 15 - 7));
    let py = Math.round(cy - bp.y * scale + (Math.random() * 15 - 7));
    px = clamp(px, 0, viewportW - cardW);
    py = clamp(py, 0, viewportH - cardH);
    return [px, py];
  });
};

class Engine {
  constructor() {
    this.running = false;
    this.phase = "shape";
    this.spawned = 0;
    this.totalSpawned = 0;
    this.positions = [];
    this.timer = null;
    this.popups = new Set();
    this.currentConfig = this.readConfig();
    updateMetrics({ mode: this.currentConfig.shapeType });
  }

  readConfig() {
    const countHeart = clamp(parseInt(inputCountHeart.value, 10) || 150, 20, 360);
    const countRandom = clamp(parseInt(inputCountRandom.value, 10) || 70, 0, 260);
    const intervalMs = clamp(parseInt(inputIntervalMs.value, 10) || 24, 10, 160);
    const ttlMs = clamp(parseInt(inputTtlMs.value, 10) || 0, 0, 12000);
    const shapeType = selectShape.value || "heart";
    const sizeScale = clamp(parseFloat(inputSizeScale.value) || 1, 0.6, 2.2);
    const customText = inputCustomMessages.value.trim();
    const activeMessages = customText ? customText.split("\n").map((s) => s.trim()).filter(Boolean) : messages;
    return { countHeart, countRandom, intervalMs, ttlMs, shapeType, sizeScale, activeMessages };
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.phase = "shape";
    this.spawned = 0;
    this.totalSpawned = 0;
    this.currentConfig = this.readConfig();

    const { w, h } = this.viewport();
    const { cardW, cardH } = this.cardSize();
    this.positions = computePositions(
      w,
      h,
      cardW,
      cardH,
      this.currentConfig.countHeart,
      this.currentConfig.shapeType,
      this.currentConfig.sizeScale
    );
    emptyState.classList.add("hidden");
    btnStart.textContent = "暂停";
    btnHeroStart.textContent = "暂停";
    updateMetrics({ status: "播放中", created: 0, visible: 0, progress: 0, mode: this.currentConfig.shapeType });
    this.schedule();
  }

  stop({ clear = false } = {}) {
    this.running = false;
    if (this.timer) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
    btnStart.textContent = "开始体验";
    btnHeroStart.textContent = "立即生成";
    updateMetrics({ status: clear ? "已清空" : "已暂停", visible: this.popups.size });
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
    for (const popup of Array.from(this.popups)) popup.dismiss(true);
    this.popups.clear();
    layer.innerHTML = "";
    emptyState.classList.remove("hidden");
    updateMetrics({ created: 0, visible: 0, progress: 0 });
  }

  viewport() {
    const rect = layer.getBoundingClientRect();
    return { w: Math.max(320, rect.width), h: Math.max(360, rect.height) };
  }

  cardSize() {
    return window.innerWidth < 720 ? { cardW: 206, cardH: 76 } : { cardW: 220, cardH: 76 };
  }

  schedule() {
    if (!this.running) return;
    this.timer = window.setTimeout(() => this.tick(), this.currentConfig.intervalMs);
  }

  tick() {
    if (!this.running) return;
    const { countHeart, countRandom, ttlMs, activeMessages } = this.currentConfig;
    const { w, h } = this.viewport();
    const { cardW, cardH } = this.cardSize();
    const totalTarget = countHeart + countRandom;

    let px;
    let py;
    if (this.phase === "shape") {
      if (this.spawned >= countHeart) {
        this.phase = "random";
        this.spawned = 0;
        this.schedule();
        return;
      }
      [px, py] = this.positions[this.spawned];
    } else {
      if (this.spawned >= countRandom) {
        this.stop();
        updateMetrics({ status: "完成", progress: 100 });
        return;
      }
      px = Math.round(Math.random() * Math.max(0, w - cardW));
      py = Math.round(Math.random() * Math.max(0, h - cardH));
    }

    const popup = new Popup({
      parent: layer,
      x: px,
      y: py,
      w: cardW,
      h: cardH,
      message: pick(activeMessages.length ? activeMessages : messages),
      bg: pick(palettes[activePreset] || palettes.gentle),
      accent: pick(["#f45b83", "#4a90e2", "#2bbf9f", "#f4b740"]),
      ttlMs,
      onDismiss: () => {
        this.popups.delete(popup);
        updateMetrics({ visible: this.popups.size });
      },
    });

    this.popups.add(popup);
    this.spawned += 1;
    this.totalSpawned += 1;
    updateMetrics({
      created: this.totalSpawned,
      visible: this.popups.size,
      progress: totalTarget ? (this.totalSpawned / totalTarget) * 100 : 100,
    });
    this.schedule();
  }
}

class Popup {
  constructor({ parent, x, y, w, h, message, bg, accent, ttlMs, onDismiss }) {
    this.el = document.createElement("div");
    this.onDismiss = onDismiss;
    this.ttlTimer = null;

    this.el.className = "popup";
    this.el.style.setProperty("--x", `${x}px`);
    this.el.style.setProperty("--y", `${y}px`);
    this.el.style.setProperty("--w", `${w}px`);
    this.el.style.setProperty("--h", `${h}px`);
    this.el.style.setProperty("--bg", bg);
    this.el.style.setProperty("--accent", accent);
    this.el.innerHTML = `
      <div class="popupCard" role="group" aria-label="祝福弹窗">
        <div class="popupHeader">
          <span class="heart">♥ Love Pop Up</span>
          <span>可点击关闭</span>
        </div>
        <button class="popupClose" type="button" aria-label="关闭">×</button>
        <div class="popupText">${escapeHtml(message)}</div>
      </div>
    `;

    this.el.querySelector(".popupClose").addEventListener("click", (event) => {
      event.stopPropagation();
      this.dismiss();
    });
    this.el.addEventListener("click", () => this.dismiss());
    parent.appendChild(this.el);

    if (ttlMs > 0) {
      this.ttlTimer = window.setTimeout(() => this.dismiss(), ttlMs);
    }
  }

  dismiss(immediate = false) {
    if (!this.el) return;
    if (this.ttlTimer) window.clearTimeout(this.ttlTimer);

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

const applyPreset = (name) => {
  const preset = presetConfig[name] || presetConfig.gentle;
  activePreset = name;
  selectShape.value = preset.shapeType;
  inputSizeScale.value = preset.sizeScale;
  inputCountHeart.value = preset.countHeart;
  inputCountRandom.value = preset.countRandom;
  inputIntervalMs.value = preset.intervalMs;
  inputTtlMs.value = preset.ttlMs;
  inputCustomMessages.value = preset.messages;
  document.querySelectorAll(".preset").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.preset === name);
  });
  updateMetrics({ mode: preset.shapeType });
};

const downloadConfig = () => {
  const config = engine.readConfig();
  const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "love-pop-up-config.json";
  link.click();
  URL.revokeObjectURL(url);
};

const renderReviews = (data) => {
  if (!data || data.length === 0) {
    reviewsList.innerHTML = `<div class="emptyReviews">暂时没有评价，欢迎留下第一条反馈</div>`;
    return;
  }
  reviewsList.innerHTML = data
    .map(
      (r) => `
        <article class="reviewItem">
          <div class="reviewItemHead">
            <div class="reviewItemName">${escapeHtml(r.name || "匿名用户")}</div>
            <div class="reviewItemDate">${new Date(`${r.created_at}Z`).toLocaleString()}</div>
          </div>
          <div class="reviewItemScore">${"★".repeat(r.score || 5)}${"☆".repeat(5 - (r.score || 5))}</div>
          <div class="reviewItemBody">${escapeHtml(r.comment || "")}</div>
        </article>
      `
    )
    .join("");
};

const fetchReviews = async () => {
  reviewsList.innerHTML = `<div class="loading">加载中...</div>`;
  try {
    const url = apiBase ? `${apiBase}/api/reviews` : "/api/reviews";
    const res = await fetch(url);
    const json = await res.json();
    renderReviews(json.ok ? json.data : []);
  } catch {
    reviewsList.innerHTML = `<div class="emptyReviews">评价加载失败，请稍后再试</div>`;
  }
};

const setRating = (value) => {
  reviewScore.value = String(value);
  starRating.querySelectorAll("button").forEach((star) => {
    const current = parseInt(star.dataset.val, 10);
    star.classList.toggle("active", current <= value);
  });
};

const engine = new Engine();

[btnStart, btnHeroStart].forEach((btn) => btn.addEventListener("click", () => engine.toggle()));
btnDemo.addEventListener("click", () => {
  applyPreset("bright");
  engine.stop({ clear: true });
  engine.start();
});
btnClear.addEventListener("click", () => engine.stop({ clear: true }));
btnReset.addEventListener("click", () => {
  engine.stop({ clear: true });
  applyPreset("gentle");
  updateMetrics({ status: "已重置", created: 0, visible: 0, progress: 0 });
});
btnScreenshot.addEventListener("click", downloadConfig);

document.querySelectorAll(".preset").forEach((btn) => {
  btn.addEventListener("click", () => applyPreset(btn.dataset.preset));
});

[selectShape, inputSizeScale].forEach((el) => {
  el.addEventListener("input", () => updateMetrics({ mode: selectShape.value }));
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") engine.stop({ clear: true });
});

window.addEventListener("resize", () => {
  if (!engine.running) return;
  const config = engine.readConfig();
  const { w, h } = engine.viewport();
  const { cardW, cardH } = engine.cardSize();
  engine.positions = computePositions(w, h, cardW, cardH, config.countHeart, config.shapeType, config.sizeScale);
});

surveyForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitSurvey();
});

btnReview.addEventListener("click", () => {
  reviewsModal.hidden = false;
  fetchReviews();
});

closeReviews.addEventListener("click", () => {
  reviewsModal.hidden = true;
});

reviewsModal.addEventListener("click", (event) => {
  if (event.target === reviewsModal) reviewsModal.hidden = true;
});

starRating.querySelectorAll("button").forEach((star) => {
  star.addEventListener("click", () => setRating(parseInt(star.dataset.val, 10)));
  star.addEventListener("mouseenter", () => {
    const value = parseInt(star.dataset.val, 10);
    starRating.querySelectorAll("button").forEach((item) => {
      item.classList.toggle("hover", parseInt(item.dataset.val, 10) <= value);
    });
  });
  star.addEventListener("mouseleave", () => {
    starRating.querySelectorAll("button").forEach((item) => item.classList.remove("hover"));
  });
});

reviewForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("reviewName").value.trim();
  const comment = $("reviewComment").value.trim();
  const score = parseInt(reviewScore.value, 10) || 5;

  if (!comment) {
    reviewHint.textContent = "请填写评论内容";
    return;
  }

  reviewSubmit.disabled = true;
  reviewHint.textContent = "提交中...";
  try {
    const url = apiBase ? `${apiBase}/api/reviews` : "/api/reviews";
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, score, comment }),
    });
    const json = await res.json();
    if (json.ok) {
      reviewHint.textContent = "提交成功";
      $("reviewComment").value = "";
      fetchReviews();
      window.setTimeout(() => {
        reviewHint.textContent = "";
      }, 1800);
    } else {
      reviewHint.textContent = "提交失败，请稍后再试";
    }
  } catch {
    reviewHint.textContent = "网络错误，请稍后再试";
  } finally {
    reviewSubmit.disabled = false;
  }
});

applyPreset("gentle");
setRating(5);
if (!surveyReady) {
  showSurvey();
} else {
  hideSurvey();
}
