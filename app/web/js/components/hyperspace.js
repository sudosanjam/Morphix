/**
 * Subtle & Amplified Ambient Hyperspace Canvas Engine.
 * Provides a visible, mesmerizing cosmic stardust drift complimentary to the dark pastel design.
 */

let canvas = null;
let ctx = null;
let stars = [];
let animId = null;
let isRunning = false;
let width = 0;
let height = 0;
let cx = 0;
let cy = 0;
let fov = 340;
let numStars = 175;
let baseSpeed = 2.0;
let currentSpeed = 2.0;
let targetSpeed = 2.0;
let speedDecay = 0.06;

let starColorRgb = "137, 180, 250";
let trailColorRgb = "203, 166, 247";

class Star {
  constructor() {
    this.phase = Math.random() * Math.PI * 2;
    this.reset(true);
  }

  reset(initial = false) {
    this.x = (Math.random() - 0.5) * (width || 1200) * 2.2;
    this.y = (Math.random() - 0.5) * (height || 800) * 2.2;
    this.z = initial ? Math.random() * 1000 + 1 : 1000;
    this.prevPx = null;
    this.prevPy = null;
    this.size = Math.random() * 1.8 + 1.1; // 1.1px to 2.9px
    this.colorVariant = Math.random() > 0.4;
    this.hasGlow = Math.random() > 0.65;
  }

  update(speed) {
    this.z -= speed;
    if (this.z <= 1) {
      this.reset();
    }
  }

  draw() {
    const k = fov / this.z;
    const px = cx + this.x * k;
    const py = cy + this.y * k;

    // Check screen boundary margins
    if (px < -30 || px > width + 30 || py < -30 || py > height + 30) {
      this.reset();
      return;
    }

    const depthRatio = 1 - (this.z / 1000);
    // Amplified alpha range: 0.25 (distant) to 0.90 (close) with delicate twinkle
    const twinkle = Math.sin(Date.now() * 0.003 + this.phase) * 0.08;
    const alpha = Math.min(0.95, Math.max(0.22, 0.28 + depthRatio * 0.62 + twinkle));
    const starRgb = this.colorVariant ? starColorRgb : trailColorRgb;

    ctx.save();

    // Stardust motion trail
    if (this.prevPx !== null && Math.abs(px - this.prevPx) < 140 && Math.abs(py - this.prevPy) < 140) {
      ctx.beginPath();
      ctx.moveTo(this.prevPx, this.prevPy);
      ctx.lineTo(px, py);
      ctx.strokeStyle = `rgba(${starRgb}, ${alpha * 0.65})`;
      ctx.lineWidth = this.size * (0.8 + depthRatio * 0.9);
      ctx.lineCap = "round";
      ctx.stroke();
    }

    // Glowing core for prominent stars
    if (this.hasGlow && depthRatio > 0.35) {
      ctx.shadowBlur = 9;
      ctx.shadowColor = `rgba(${starRgb}, ${alpha * 0.85})`;
    }

    // Star point particle
    ctx.beginPath();
    ctx.arc(px, py, this.size * (0.65 + depthRatio * 0.75), 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${starRgb}, ${alpha})`;
    ctx.fill();

    ctx.restore();

    this.prevPx = px;
    this.prevPy = py;
  }
}

function updateThemeColors() {
  const root = getComputedStyle(document.documentElement);
  const starVar = root.getPropertyValue("--hyperspace-star-rgb").trim();
  const trailVar = root.getPropertyValue("--hyperspace-trail-rgb").trim();
  if (starVar) starColorRgb = starVar;
  if (trailVar) trailColorRgb = trailVar;
}

function handleResize() {
  if (!canvas) return;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  width = window.innerWidth || document.documentElement.clientWidth || 1280;
  height = window.innerHeight || document.documentElement.clientHeight || 800;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(dpr, dpr);

  cx = width / 2;
  cy = height / 2;
  fov = Math.max(300, Math.min(width, height) * 0.5);
}

function renderLoop() {
  if (!isRunning) return;

  // Clear canvas smoothly
  ctx.clearRect(0, 0, width, height);

  // Smooth speed interpolation (easing back down from warp pulse)
  if (currentSpeed > targetSpeed) {
    currentSpeed = Math.max(targetSpeed, currentSpeed - speedDecay);
  }

  for (let i = 0; i < stars.length; i++) {
    stars[i].update(currentSpeed);
    stars[i].draw();
  }

  animId = requestAnimationFrame(renderLoop);
}

export function initHyperspace() {
  canvas = document.getElementById("hyperspace-canvas");
  if (!canvas) return;
  ctx = canvas.getContext("2d");

  // Check user preference for reduced motion
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const userDisabled = localStorage.getItem("morphix_hyperspace") === "false";

  if (prefersReduced || userDisabled) {
    canvas.classList.add("hidden");
    return;
  }

  handleResize();
  updateThemeColors();

  // Create star pool
  stars = [];
  for (let i = 0; i < numStars; i++) {
    stars.push(new Star());
  }

  window.addEventListener("resize", handleResize);

  // Pause when tab/window is hidden to save zero battery
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopHyperspace();
    } else {
      const enabled = localStorage.getItem("morphix_hyperspace") !== "false";
      if (enabled) startHyperspace();
    }
  });

  // Watch for theme palette changes
  const observer = new MutationObserver(() => updateThemeColors());
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-palette", "data-theme"] });

  startHyperspace();

  // Expose pulse to window
  window.hyperspacePulse = hyperspacePulse;
}

export function startHyperspace() {
  if (isRunning) return;
  if (!canvas) return;
  canvas.classList.remove("hidden");
  isRunning = true;
  currentSpeed = baseSpeed;
  targetSpeed = baseSpeed;
  animId = requestAnimationFrame(renderLoop);
}

export function stopHyperspace() {
  isRunning = false;
  if (animId) {
    cancelAnimationFrame(animId);
    animId = null;
  }
}

export function toggleHyperspace(enabled) {
  if (enabled === undefined) {
    enabled = !isRunning;
  }

  localStorage.setItem("morphix_hyperspace", enabled ? "true" : "false");

  if (enabled) {
    if (canvas) canvas.classList.remove("hidden");
    startHyperspace();
  } else {
    stopHyperspace();
    if (canvas) canvas.classList.add("hidden");
  }

  return enabled;
}

export function hyperspacePulse(multiplier = 2.8) {
  if (!isRunning) return;
  currentSpeed = baseSpeed * multiplier;
  updateThemeColors();
}
