"use strict";

/* =========================================
   DIGITAL LIFE — ECOSYSTEM DASHBOARD
   Python is authoritative.
   JavaScript only fetches and renders state.
   ========================================= */

const API_URL = "http://127.0.0.1:8000/simulation/state";
const CONFIG_URL = "http://127.0.0.1:8000/simulation/config";
const STATUS_URL = "http://127.0.0.1:8000/simulation/status";
const HISTORY_URL = "http://127.0.0.1:8000/simulation/metrics/history?limit=120";
const ORGANISM_URL = "http://127.0.0.1:8000/simulation/organisms";
const PAUSE_URL = "http://127.0.0.1:8000/simulation/pause";
const RESUME_URL = "http://127.0.0.1:8000/simulation/resume";
const STEP_URL = "http://127.0.0.1:8000/simulation/step";
const RESET_URL = "http://127.0.0.1:8000/simulation/reset";

const canvas = document.getElementById("ecosystem-canvas");
const ctx = canvas.getContext("2d");

const loadingOverlay = document.getElementById("world-loading");
const connectionIndicator = document.getElementById("connection-indicator");
const connectionText = document.getElementById("connection-text");

const WORLD_BACKGROUND = "#080f14";
const GRID_COLOR = "rgba(130, 160, 175, 0.055)";
const SELECTED_COLOR = "#ffffff";

const ORGANISM_NATIVE_SIZE = 8;
const ORGANISM_SMALL_SCALE = 2;
const ORGANISM_LARGE_SCALE = 3;
const FOOD_SCALE = 2;

const POLL_INTERVAL_MS = 1000;
const MAX_PIXEL_RATIO = 2;
const MIN_ORGANISM_RADIUS = 8;

let latestState = null;
let selectedOrganismId = null;
let isFetching = false;
let consecutiveFailures = 0;
let hasInitializedCanvas = false;

/* Request sequencing: stale responses never overwrite newer state. */
let stateRequestId = 0;
let lastAppliedRequestId = 0;

/* Status + history polling (independent from state polling). */
let isStatusFetching = false;
let isHistoryFetching = false;
let statePollCount = 0;
let lastHistoryTick = null;

/* Control-request guards: one operation of each kind at a time. */
let controlBusy = {
    pause: false,
    resume: false,
    step: false,
    reset: false,
};

let lastBackendStatus = null;

let canvasWidth = 800;
let canvasHeight = 600;

let currentTicksPerSecond = null;
let minTicksPerSecond = 0.5;
let maxTicksPerSecond = 60;
let isApplyingTicks = false;


/* =========================================
   DOM HELPERS
   ========================================= */

function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}

function formatNumber(value, digits = 2) {
    if (value === null || value === undefined) {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toLocaleString(undefined, {
        maximumFractionDigits: digits
    });
}

function formatInteger(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return Math.round(number).toLocaleString();
}


/* =========================================
   CONNECTION STATUS
   ========================================= */

function setConnectionStatus(connected, message) {
    connectionIndicator.classList.toggle("connected", connected);
    connectionIndicator.classList.toggle("disconnected", !connected);

    connectionText.textContent = message;
}

function setLoadingMessage(message) {
    loadingOverlay.replaceChildren();

    const paragraph = document.createElement("p");
    paragraph.textContent = message;

    loadingOverlay.appendChild(paragraph);
    loadingOverlay.hidden = false;
}

function hideLoadingMessage() {
    loadingOverlay.hidden = true;
}


/* =========================================
   SIMULATION STATUS PANEL
   Uses actual backend responses only.
   ========================================= */

function updateStatusPanel(status) {
    if (!status || typeof status !== "object") {
        return;
    }

    lastBackendStatus = status;

    const simStatus = status.simulation_status
        || (status.paused ? "paused" : null);

    if (simStatus === "paused") {
        setText("simulation-status", "Paused");
    } else if (simStatus === "running") {
        setText("simulation-status", "Running");
    } else if (simStatus === "idle") {
        setText("simulation-status", "Idle");
    }

    if (status.worker_alive === true) {
        setText("worker-health", "Healthy");
    } else if (status.worker_alive === false) {
        setText("worker-health", "Stopped");
    }

    if (Number.isFinite(Number(status.ticks_per_second))) {
        setText("tick-rate", `${Number(status.ticks_per_second)}/s`);
    }

    if (status.last_tick === null
        || status.last_tick === undefined) {
        setText("last-tick", "—");
    } else {
        setText("last-tick", formatInteger(status.last_tick));
    }

    const workerError = document.getElementById("worker-error");

    if (workerError) {
        if (typeof status.last_error === "string"
            && status.last_error.length > 0) {
            workerError.textContent = `Worker error: ${status.last_error}`;
            workerError.hidden = false;
        } else {
            workerError.textContent = "";
            workerError.hidden = true;
        }
    }
}

function markDataFreshness(isStale) {
    if (isStale) {
        setText("data-freshness", "Stale");
    } else if (latestState) {
        setText("data-freshness", "Live");
    } else {
        setText("data-freshness", "—");
    }
}


/* =========================================
   SIMULATION CONTROLS
   The browser never advances the simulation;
   every button delegates to a backend endpoint.
   ========================================= */

function getControlElements() {
    return {
        pauseButton: document.getElementById("pause-button"),
        resumeButton: document.getElementById("resume-button"),
        stepButton: document.getElementById("step-button"),
        resetButton: document.getElementById("reset-button"),
        status: document.getElementById("control-status"),
        error: document.getElementById("control-error"),
    };
}

function setControlStatus(message) {
    const { status } = getControlElements();

    if (status) {
        status.textContent = message || "";
    }
}

function setControlError(message) {
    const { error } = getControlElements();

    if (!error) {
        return;
    }

    if (!message) {
        error.textContent = "";
        error.hidden = true;
        return;
    }

    error.textContent = message;
    error.hidden = false;
}

function setControlsBusy(busy) {
    const {
        pauseButton,
        resumeButton,
        stepButton,
        resetButton,
    } = getControlElements();

    for (const button of [pauseButton, resumeButton, stepButton, resetButton]) {
        if (button) {
            button.disabled = busy;
        }
    }
}

function controlErrorMessage(error, fallback) {
    if (error && typeof error.message === "string"
        && error.message.length > 0
        && error.message !== "Failed to fetch") {
        return error.message;
    }

    return fallback;
}

async function postControl(url, kind, workingMessage, successMessage) {
    if (controlBusy[kind]) {
        return false;
    }

    controlBusy[kind] = true;
    setControlsBusy(true);
    setControlError(null);
    setControlStatus(workingMessage);

    try {
        const response = await fetch(url, {
            method: "POST",
            cache: "no-store",
        });

        if (!response.ok) {
            let detail = `Request failed with HTTP ${response.status}.`;

            try {
                const errorBody = await response.json();

                if (typeof errorBody.detail === "string") {
                    detail = errorBody.detail;
                }
            } catch {
                // Keep the HTTP status message.
            }

            if (response.status === 409) {
                setControlError(
                    "Single-step needs a paused simulation. "
                    + "Pause first, then step once. "
                    + `(${detail})`
                );
            } else {
                setControlError(detail);
            }

            setControlStatus("");
            return false;
        }

        const result = await response.json();

        updateStatusPanel(result.status || result);
        setControlStatus(successMessage);
        await refreshStateNow();

        return true;
    } catch (error) {
        console.error(`Control request failed (${kind}):`, error);
        setControlError(controlErrorMessage(
            error,
            "Could not reach the backend. The last valid state is still shown."
        ));
        setControlStatus("");
        return false;
    } finally {
        controlBusy[kind] = false;
        setControlsBusy(false);
    }
}

async function refreshStateNow() {
    statePollCount += 1;
    await fetchSimulationState();
    await fetchSimulationStatus();
}

function initializeControls() {
    const {
        pauseButton,
        resumeButton,
        stepButton,
        resetButton,
    } = getControlElements();

    if (!pauseButton || !resumeButton || !stepButton || !resetButton) {
        return;
    }

    pauseButton.addEventListener("click", () => {
        postControl(
            PAUSE_URL,
            "pause",
            "Pausing…",
            "Simulation paused. Ticks are no longer advancing."
        );
    });

    resumeButton.addEventListener("click", () => {
        postControl(
            RESUME_URL,
            "resume",
            "Resuming…",
            "Simulation resumed."
        );
    });

    stepButton.addEventListener("click", () => {
        postControl(
            STEP_URL,
            "step",
            "Advancing one tick…",
            "Advanced exactly one tick."
        );
    });

    resetButton.addEventListener("click", () => {
        postControl(
            RESET_URL,
            "reset",
            "Resetting…",
            "Simulation reset to its configured initial state."
        );
    });
}


/* =========================================
   STATUS POLLING (independent cadence)
   ========================================= */

async function fetchSimulationStatus() {
    if (isStatusFetching) {
        return;
    }

    isStatusFetching = true;

    try {
        const response = await fetch(STATUS_URL, {
            method: "GET",
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error(`Status API returned HTTP ${response.status}.`);
        }

        updateStatusPanel(await response.json());
    } catch (error) {
        // Status is best-effort; the state poll owns connection errors.
        console.error("Failed to fetch simulation status:", error);
    } finally {
        isStatusFetching = false;
    }
}


/* =========================================
   CANVAS INITIALIZATION
   ========================================= */

function resizeCanvas() {
    if (!latestState) {
        return;
    }

    const world = latestState.world;

    canvasWidth = world.width;
    canvasHeight = world.height;

    const pixelRatio = Math.min(
        window.devicePixelRatio || 1,
        MAX_PIXEL_RATIO
    );

    canvas.width = Math.round(canvasWidth * pixelRatio);
    canvas.height = Math.round(canvasHeight * pixelRatio);

    /*
     * CSS controls the visible canvas dimensions.
     * The backing canvas uses a higher resolution
     * where necessary for sharper rendering.
     */

    ctx.setTransform(
        pixelRatio,
        0,
        0,
        pixelRatio,
        0,
        0
    );

    renderWorld();
}


/* =========================================
   WORLD RENDERING
   ========================================= */

function drawBackground() {
    ctx.fillStyle = WORLD_BACKGROUND;

    ctx.fillRect(
        0,
        0,
        canvasWidth,
        canvasHeight
    );

    /*
     * Draw a subtle reference grid.
     * This is purely visual and does not affect physics.
     */

    const gridSize = 50;

    ctx.beginPath();
    ctx.strokeStyle = GRID_COLOR;
    ctx.lineWidth = 1;

    for (let x = 0; x <= canvasWidth; x += gridSize) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvasHeight);
    }

    for (let y = 0; y <= canvasHeight; y += gridSize) {
        ctx.moveTo(0, y);
        ctx.lineTo(canvasWidth, y);
    }

    ctx.stroke();
}

/* =========================================
   SPRITE BITMAPS (pre-rendered offscreen)
   Python remains authoritative for state;
   these bitmaps are display-only.
   ========================================= */

let foodSprite = null;
let organismSprite = null;
let deadSprite = null;

/*
 * Populous-style 16-bit followers: hand-plotted pixel maps,
 * tiny palettes, no anti-aliasing. Blitted with smoothing off
 * at integer scales so pixels stay crisp.
 * K=outline G=body L=light D=shade W=eye P=pupil N=nucleus.
 * Follower faces right.
 */
const ORGANISM_PIXELS = [
    "..KKKK..",
    ".KLGGLK.",
    "KGGGLLPK",
    "KGNGGLLK",
    "KGNGLLPK",
    "KGGGDLLK",
    ".KDDDDK.",
    "..KKKK..",
];

const ORGANISM_PALETTE = {
    K: "#07120d",
    G: "#35c184",
    L: "#8ff5c3",
    D: "#14563c",
    W: "#ffffff",
    P: "#0b1510",
    N: "#0c2b22",
};

/*
 * Same silhouette, dead: grey flesh, dim highlight, red snap
 * pixels in the eye sockets, cracked nucleus row.
 */
const DEAD_PIXELS = [
    "..KKKK..",
    ".KlGGlK.",
    "KGGGllRK",
    "KGNGGllK",
    "KGNGllRK",
    "KGGGDllK",
    ".KDDDDK.",
    "..KKKK..",
];

const DEAD_PALETTE = {
    K: "#10161b",
    G: "#59636e",
    l: "#9aa5b1",
    D: "#2b3238",
    R: "#ff7777",
    N: "#141a1f",
};

/* Food berry with leaf and stem. */
const FOOD_PIXELS = [
    "..GL..",
    "..K...",
    "..KK..",
    ".KYYK.",
    "KYWYYK",
    "KYYYYK",
    ".KDDK.",
];

const FOOD_PALETTE = {
    K: "#4a2f0b",
    Y: "#f4c95d",
    W: "#fff3c4",
    D: "#8a5f10",
    G: "#2e8b57",
    L: "#8ff5c3",
};

function makePixelSprite(rows, palette) {
    const sprite = document.createElement("canvas");
    sprite.width = rows[0].length;
    sprite.height = rows.length;

    const g = sprite.getContext("2d");

    for (let y = 0; y < rows.length; y++) {
        const row = rows[y];

        for (let x = 0; x < row.length; x++) {
            const color = palette[row[x]];

            if (!color) {
                continue;
            }

            g.fillStyle = color;
            g.fillRect(x, y, 1, 1);
        }
    }

    return sprite;
}

function getFoodSprite() {
    if (!foodSprite) {
        foodSprite = makePixelSprite(FOOD_PIXELS, FOOD_PALETTE);
    }

    return foodSprite;
}

function getOrganismSprite() {
    if (!organismSprite) {
        organismSprite = makePixelSprite(ORGANISM_PIXELS, ORGANISM_PALETTE);
    }

    return organismSprite;
}

function getDeadSprite() {
    if (!deadSprite) {
        deadSprite = makePixelSprite(DEAD_PIXELS, DEAD_PALETTE);
    }

    return deadSprite;
}

/* Small folk render at 2x (16px), big folk at 3x (24px). */
function organismPixelScale(organism) {
    const size = Number(organism.genome?.size);

    if (!Number.isFinite(size)) {
        return ORGANISM_SMALL_SCALE;
    }

    return size < 0.5 ? ORGANISM_SMALL_SCALE : ORGANISM_LARGE_SCALE;
}


function pixelDrawFood(foodItems) {
    const sprite = getFoodSprite();
    const w = sprite.width * FOOD_SCALE;
    const h = sprite.height * FOOD_SCALE;

    ctx.save();

    for (const food of foodItems) {
        if (!Number.isFinite(food.x) || !Number.isFinite(food.y)) {
            continue;
        }

        ctx.drawImage(sprite, food.x - w / 2, food.y - h / 2, w, h);
    }

    ctx.restore();
}

function pixelOrganismRadius(organism) {
    /*
     * Genome size is currently normalized between 0 and 1.
     * Small folk are 16px, big folk 24px. This radius is a
     * display choice, not a change to physical size.
     */

    return organismPixelScale(organism) * (ORGANISM_NATIVE_SIZE / 2);
}

function drawGlow(x, y, radius, color) {
    const glow = ctx.createRadialGradient(x, y, 1, x, y, radius);
    glow.addColorStop(0, color);
    glow.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = glow;
    ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2);
}

function pixelDrawOrganism(organism) {
    if (
        !Number.isFinite(organism.x) ||
        !Number.isFinite(organism.y)
    ) {
        return;
    }

    const isAlive = organism.alive && organism.health > 0;
    const isSelected = organism.organism_id === selectedOrganismId
        || organism.id === selectedOrganismId;

    const scale = organismPixelScale(organism);
    const sprite = isAlive ? getOrganismSprite() : getDeadSprite();
    const w = sprite.width * scale;
    const h = sprite.height * scale;

    /*
     * One-native-pixel hop alternating per tick: a
     * Populous-style waddle. Dead carcasses stay still.
     */

    let bob = 0;

    if (isAlive && latestState && Number.isFinite(latestState.tick)) {
        bob = (((latestState.tick >> 2) + (Number(organism.id) || 0)) & 1) * -scale;
    }

    ctx.save();

    ctx.globalAlpha = isAlive ? 1 : 0.9;

    if (isAlive) {
        drawGlow(organism.x, organism.y + bob, w * 0.9, "rgba(85, 230, 165, 0.20)");
    } else {
        drawGlow(organism.x, organism.y, w * 0.8, "rgba(255, 119, 119, 0.07)");
    }

    ctx.drawImage(sprite, organism.x - w / 2, organism.y - h / 2 + bob, w, h);

    if (isSelected) {
        ctx.globalAlpha = 1;
        ctx.strokeStyle = SELECTED_COLOR;
        ctx.lineWidth = 2;
        ctx.strokeRect(
            organism.x - w / 2 - 3,
            organism.y - h / 2 + bob - 3,
            w + 6,
            h + 6
        );
    }

    ctx.restore();
}
/* =========================================
   RENDER STYLE: CLASSIC DOTS (original)
   Flat colored circles. The very first look.
   ========================================= */

const DOTS_ORGANISM_COLOR = "#55e6a5";
const DOTS_FOOD_COLOR = "#f4c95d";
const DOTS_DEAD_COLOR = "#ff7777";
const DOTS_MIN_RADIUS = 3;

function dotsOrganismRadius(organism) {
    const size = Number(organism.genome?.size);

    if (!Number.isFinite(size)) {
        return DOTS_MIN_RADIUS;
    }

    return DOTS_MIN_RADIUS + size * 3;
}

function dotsDrawFood(foodItems) {
    ctx.save();

    for (const food of foodItems) {
        if (!Number.isFinite(food.x) || !Number.isFinite(food.y)) {
            continue;
        }

        ctx.beginPath();
        ctx.fillStyle = DOTS_FOOD_COLOR;
        ctx.arc(food.x, food.y, 2.5, 0, Math.PI * 2);
        ctx.fill();
    }

    ctx.restore();
}

function dotsDrawOrganism(organism) {
    if (
        !Number.isFinite(organism.x) ||
        !Number.isFinite(organism.y)
    ) {
        return;
    }

    const isAlive = organism.alive && organism.health > 0;
    const isSelected = organism.organism_id === selectedOrganismId
        || organism.id === selectedOrganismId;

    const radius = dotsOrganismRadius(organism);

    ctx.save();
    ctx.globalAlpha = isAlive ? 1 : 0.4;

    ctx.beginPath();

    if (isSelected) {
        ctx.fillStyle = SELECTED_COLOR;
    } else {
        ctx.fillStyle = isAlive ? DOTS_ORGANISM_COLOR : DOTS_DEAD_COLOR;
    }

    ctx.arc(organism.x, organism.y, radius, 0, Math.PI * 2);
    ctx.fill();

    if (isSelected) {
        ctx.globalAlpha = 1;
        ctx.beginPath();
        ctx.strokeStyle = SELECTED_COLOR;
        ctx.lineWidth = 1.5;
        ctx.arc(organism.x, organism.y, radius + 5, 0, Math.PI * 2);
        ctx.stroke();
    }

    ctx.restore();
}


/* =========================================
   RENDER STYLE: LAB CELLS (vector sprites)
   Pre-rendered glossy cells with cilia, nucleus
   and eyes; berry food; gentle pulse.
   ========================================= */

const CELL_FOOD_SIZE = 24;
const CELL_CREATURE_SIZE = 64;
const CELL_FOOD_DISPLAY = 11;
const CELL_MIN_RADIUS = 5;
const CELL_SPRITE_PADDING = 14;

let cellFoodSprite = null;
let cellOrganismSprite = null;
let cellDeadSprite = null;

function cellMakeSprite(size, painter) {
    const sprite = document.createElement("canvas");
    sprite.width = size;
    sprite.height = size;

    const g = sprite.getContext("2d");
    painter(g, size);

    return sprite;
}

function paintCellFood(g, size) {
    const cx = size / 2;
    const cy = size / 2 + 1;

    const glow = g.createRadialGradient(cx, cy, 1, cx, cy, 11);
    glow.addColorStop(0, "rgba(244, 201, 93, 0.45)");
    glow.addColorStop(1, "rgba(244, 201, 93, 0)");
    g.fillStyle = glow;
    g.fillRect(0, 0, size, size);

    g.fillStyle = "rgba(0, 0, 0, 0.35)";
    g.beginPath();
    g.ellipse(cx, cy + 7, 5.5, 2, 0, 0, Math.PI * 2);
    g.fill();

    const body = g.createRadialGradient(cx - 2, cy - 2.5, 1, cx, cy, 7);
    body.addColorStop(0, "#fff3c4");
    body.addColorStop(0.45, "#f4c95d");
    body.addColorStop(1, "#8a5f10");
    g.fillStyle = body;
    g.beginPath();
    g.arc(cx, cy, 6.2, 0, Math.PI * 2);
    g.fill();
    g.lineWidth = 1.2;
    g.strokeStyle = "#6b4a0d";
    g.stroke();

    g.fillStyle = "rgba(122, 84, 16, 0.7)";
    g.beginPath();
    g.arc(cx - 1.5, cy + 1.5, 0.9, 0, Math.PI * 2);
    g.fill();
    g.beginPath();
    g.arc(cx + 2.2, cy + 0.4, 0.7, 0, Math.PI * 2);
    g.fill();

    g.strokeStyle = "#7a4a1e";
    g.lineWidth = 1.4;
    g.beginPath();
    g.moveTo(cx, cy - 6);
    g.lineTo(cx + 2.5, cy - 8.5);
    g.stroke();

    g.save();
    g.translate(cx + 4.5, cy - 8);
    g.rotate(-0.5);
    g.fillStyle = "#55e6a5";
    g.strokeStyle = "#1d5c4a";
    g.lineWidth = 1;
    g.beginPath();
    g.ellipse(0, 0, 3.4, 1.8, 0, 0, Math.PI * 2);
    g.fill();
    g.stroke();
    g.restore();

    g.fillStyle = "rgba(255, 255, 255, 0.9)";
    g.beginPath();
    g.arc(cx - 2.2, cy - 2.4, 1.5, 0, Math.PI * 2);
    g.fill();
}

function paintCellCilia(g, cx, cy, count, inner, outer, fill, stroke) {
    for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2 + Math.PI / count;
        const tipX = cx + Math.cos(angle) * outer;
        const tipY = cy + Math.sin(angle) * outer;
        const baseA = angle - 0.16;
        const baseB = angle + 0.16;

        g.beginPath();
        g.moveTo(cx + Math.cos(baseA) * inner, cy + Math.sin(baseA) * inner);
        g.lineTo(tipX, tipY);
        g.lineTo(cx + Math.cos(baseB) * inner, cy + Math.sin(baseB) * inner);
        g.closePath();
        g.fillStyle = fill;
        g.fill();

        if (stroke) {
            g.lineWidth = 0.8;
            g.strokeStyle = stroke;
            g.stroke();
        }
    }
}

function paintCellOrganism(g, size) {
    const cx = size / 2;
    const cy = size / 2;

    const glow = g.createRadialGradient(cx, cy, 4, cx, cy, 30);
    glow.addColorStop(0, "rgba(85, 230, 165, 0.30)");
    glow.addColorStop(1, "rgba(85, 230, 165, 0)");
    g.fillStyle = glow;
    g.fillRect(0, 0, size, size);

    paintCellCilia(g, cx, cy, 8, 16, 23, "#256b53", "rgba(85, 230, 165, 0.55)");

    const membrane = g.createRadialGradient(cx - 5, cy - 6, 2, cx, cy, 18);
    membrane.addColorStop(0, "#1c4a3a");
    membrane.addColorStop(0.75, "#12372b");
    membrane.addColorStop(1, "#0a241d");
    g.fillStyle = membrane;
    g.beginPath();
    g.arc(cx, cy, 17, 0, Math.PI * 2);
    g.fill();
    g.lineWidth = 3;
    g.strokeStyle = "#55e6a5";
    g.stroke();

    const cyto = g.createRadialGradient(cx - 3, cy - 4, 1, cx, cy, 14);
    cyto.addColorStop(0, "#54e8a6");
    cyto.addColorStop(0.55, "#2fbf82");
    cyto.addColorStop(1, "#1a7250");
    g.fillStyle = cyto;
    g.beginPath();
    g.arc(cx, cy, 13.5, 0, Math.PI * 2);
    g.fill();

    g.strokeStyle = "rgba(255, 255, 255, 0.55)";
    g.lineWidth = 2;
    g.beginPath();
    g.arc(cx, cy, 14.5, Math.PI * 1.05, Math.PI * 1.45);
    g.stroke();

    g.fillStyle = "#0a241d";
    g.strokeStyle = "rgba(85, 230, 165, 0.9)";
    g.lineWidth = 1.4;
    g.beginPath();
    g.ellipse(cx - 5, cy + 4, 6, 5, 0.3, 0, Math.PI * 2);
    g.fill();
    g.stroke();
    g.fillStyle = "#55e6a5";
    g.beginPath();
    g.arc(cx - 6, cy + 3, 1.8, 0, Math.PI * 2);
    g.fill();

    const eyes = [[5, -5], [5, 5]];
    for (const [dx, dy] of eyes) {
        const ex = cx + dx;
        const ey = cy + dy;
        g.fillStyle = "#ffffff";
        g.strokeStyle = "#0a241d";
        g.lineWidth = 1.2;
        g.beginPath();
        g.arc(ex, ey, 4.1, 0, Math.PI * 2);
        g.fill();
        g.stroke();
        g.fillStyle = "#0b1510";
        g.beginPath();
        g.arc(ex + 1.5, ey, 2, 0, Math.PI * 2);
        g.fill();
        g.fillStyle = "#ffffff";
        g.beginPath();
        g.arc(ex + 2.1, ey - 0.7, 0.7, 0, Math.PI * 2);
        g.fill();
    }
}

function paintCellDead(g, size) {
    const cx = size / 2;
    const cy = size / 2;

    const halo = g.createRadialGradient(cx, cy, 4, cx, cy, 28);
    halo.addColorStop(0, "rgba(255, 119, 119, 0.10)");
    halo.addColorStop(1, "rgba(255, 119, 119, 0)");
    g.fillStyle = halo;
    g.fillRect(0, 0, size, size);

    paintCellCilia(g, cx, cy, 8, 16, 20, "#3a444e", "rgba(122, 133, 143, 0.5)");

    g.fillStyle = "#2b3238";
    g.beginPath();
    g.arc(cx, cy, 17, 0, Math.PI * 2);
    g.fill();
    g.lineWidth = 3;
    g.strokeStyle = "#5b6570";
    g.stroke();

    const cyto = g.createRadialGradient(cx - 3, cy - 4, 1, cx, cy, 14);
    cyto.addColorStop(0, "#6d7883");
    cyto.addColorStop(0.6, "#4a545e");
    cyto.addColorStop(1, "#333b43");
    g.fillStyle = cyto;
    g.beginPath();
    g.arc(cx, cy, 13.5, 0, Math.PI * 2);
    g.fill();

    g.strokeStyle = "#161c20";
    g.lineWidth = 1.6;
    g.beginPath();
    g.moveTo(cx - 11, cy - 6);
    g.lineTo(cx - 4, cy - 1);
    g.lineTo(cx - 8, cy + 7);
    g.stroke();

    g.fillStyle = "#1c2227";
    g.strokeStyle = "#7a858f";
    g.lineWidth = 1.4;
    g.beginPath();
    g.ellipse(cx - 5, cy + 4, 6, 5, 0.3, 0, Math.PI * 2);
    g.fill();
    g.stroke();

    const eyes = [[5, -5], [5, 5]];
    for (const [dx, dy] of eyes) {
        const ex = cx + dx;
        const ey = cy + dy;
        g.fillStyle = "#232a30";
        g.strokeStyle = "#161c20";
        g.lineWidth = 1.2;
        g.beginPath();
        g.arc(ex, ey, 4.1, 0, Math.PI * 2);
        g.fill();
        g.stroke();
        g.strokeStyle = "#ff7777";
        g.lineWidth = 2.2;
        g.lineCap = "round";
        const s = 2.4;
        g.beginPath();
        g.moveTo(ex - s, ey - s);
        g.lineTo(ex + s, ey + s);
        g.moveTo(ex + s, ey - s);
        g.lineTo(ex - s, ey + s);
        g.stroke();
    }
}

function getCellFoodSprite() {
    if (!cellFoodSprite) {
        cellFoodSprite = cellMakeSprite(CELL_FOOD_SIZE, paintCellFood);
    }
    return cellFoodSprite;
}

function getCellOrganismSprite() {
    if (!cellOrganismSprite) {
        cellOrganismSprite = cellMakeSprite(CELL_CREATURE_SIZE, paintCellOrganism);
    }
    return cellOrganismSprite;
}

function getCellDeadSprite() {
    if (!cellDeadSprite) {
        cellDeadSprite = cellMakeSprite(CELL_CREATURE_SIZE, paintCellDead);
    }
    return cellDeadSprite;
}

function cellOrganismRadius(organism) {
    const size = Number(organism.genome?.size);

    if (!Number.isFinite(size)) {
        return CELL_MIN_RADIUS;
    }

    return CELL_MIN_RADIUS + size * 5;
}

function cellDrawFood(foodItems) {
    const sprite = getCellFoodSprite();
    const s = CELL_FOOD_DISPLAY;

    for (const food of foodItems) {
        if (!Number.isFinite(food.x) || !Number.isFinite(food.y)) {
            continue;
        }

        ctx.drawImage(sprite, food.x - s / 2, food.y - s / 2, s, s);
    }
}

function cellDrawOrganism(organism) {
    if (
        !Number.isFinite(organism.x) ||
        !Number.isFinite(organism.y)
    ) {
        return;
    }

    const isAlive = organism.alive && organism.health > 0;
    const isSelected = organism.organism_id === selectedOrganismId
        || organism.id === selectedOrganismId;

    const radius = cellOrganismRadius(organism);
    const sprite = isAlive ? getCellOrganismSprite() : getCellDeadSprite();

    let display = radius * 2 + CELL_SPRITE_PADDING;

    if (isAlive && latestState && Number.isFinite(latestState.tick)) {
        const phase = (latestState.tick / 4) + (Number(organism.id) || 0);
        display *= 1 + 0.04 * Math.sin(phase);
    }

    ctx.save();
    ctx.globalAlpha = isAlive ? 1 : 0.85;

    ctx.drawImage(
        sprite,
        organism.x - display / 2,
        organism.y - display / 2,
        display,
        display
    );

    if (isSelected) {
        ctx.globalAlpha = 1;
        ctx.beginPath();
        ctx.strokeStyle = SELECTED_COLOR;
        ctx.lineWidth = 2;
        ctx.arc(organism.x, organism.y, radius + 7, 0, Math.PI * 2);
        ctx.stroke();
    }

    ctx.restore();
}


/* =========================================
   RENDER STYLE: AMIIBO FIGURES (realistic)
   Glossy collectible figurines on NFC-stand
   bases: chibi creature, cute reflective eyes,
   rim light, sprout. Dead figures are grey,
   tilted, X-eyed with a cracked head.
   Food is a glossy golden apple.
   ========================================= */

const AMIIBO_MIN_RADIUS = 6;

function amiiboOrganismRadius(organism) {
    const size = Number(organism.genome?.size);

    if (!Number.isFinite(size)) {
        return AMIIBO_MIN_RADIUS;
    }

    return AMIIBO_MIN_RADIUS + size * 5;
}

function amiiboPalette(isAlive) {
    if (isAlive) {
        return {
            headLight: "#a9f5cd",
            headMid: "#3fd08c",
            headDark: "#14563c",
            bodyLight: "#7defb4",
            bodyMid: "#2fbf82",
            bodyDark: "#0e3a2b",
            rim: "#55e6a5",
            baseTop: "#1c2b25",
            baseSide: "#0d1412",
            baseEdge: "#55e6a5",
            leaf: "#3fd08c",
            leafDark: "#14563c",
            cheek: "rgba(255, 130, 150, 0.55)",
        };
    }

    return {
        headLight: "#c3ccd4",
        headMid: "#6d7883",
        headDark: "#2b3238",
        bodyLight: "#9aa5b1",
        bodyMid: "#4a545e",
        bodyDark: "#1c2227",
        rim: "#5b6570",
        baseTop: "#2b333b",
        baseSide: "#141a1f",
        baseEdge: "#5b6570",
        leaf: "#5b6570",
        leafDark: "#2b3238",
        cheek: "rgba(0, 0, 0, 0)",
    };
}

function amiiboDrawFood(foodItems) {
    ctx.save();

    for (const food of foodItems) {
        if (!Number.isFinite(food.x) || !Number.isFinite(food.y)) {
            continue;
        }

        const x = food.x;
        const y = food.y;

        ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
        ctx.beginPath();
        ctx.ellipse(x, y + 6, 5.5, 2, 0, 0, Math.PI * 2);
        ctx.fill();

        const body = ctx.createRadialGradient(x - 2, y - 2, 1, x, y, 6.5);
        body.addColorStop(0, "#fff3c4");
        body.addColorStop(0.5, "#f4c95d");
        body.addColorStop(1, "#8a5f10");
        ctx.fillStyle = body;
        ctx.beginPath();
        ctx.arc(x, y, 5.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.lineWidth = 1.2;
        ctx.strokeStyle = "#5c3d0c";
        ctx.stroke();

        ctx.strokeStyle = "#7a4a1e";
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(x, y - 5);
        ctx.lineTo(x + 2, y - 8);
        ctx.stroke();

        ctx.fillStyle = "#55e6a5";
        ctx.strokeStyle = "#1d5c4a";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.ellipse(x + 4, y - 7.5, 3, 1.6, -0.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
        ctx.beginPath();
        ctx.arc(x - 1.8, y - 2, 1.4, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = "rgba(255, 255, 255, 0.75)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x + 8, y - 10);
        ctx.lineTo(x + 8, y - 6);
        ctx.moveTo(x + 6, y - 8);
        ctx.lineTo(x + 10, y - 8);
        ctx.stroke();
    }

    ctx.restore();
}

function amiiboDrawOrganism(organism) {
    if (
        !Number.isFinite(organism.x) ||
        !Number.isFinite(organism.y)
    ) {
        return;
    }

    const isAlive = organism.alive && organism.health > 0;
    const isSelected = organism.organism_id === selectedOrganismId
        || organism.id === selectedOrganismId;

    const radius = amiiboOrganismRadius(organism);
    const u = radius / 8;
    const pal = amiiboPalette(isAlive);

    const cx = organism.x;
    const baseY = organism.y + radius * 0.9;

    ctx.save();

    if (!isAlive) {
        ctx.globalAlpha = 0.94;
    }

    // Floor shadow.
    ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
    ctx.beginPath();
    ctx.ellipse(cx, baseY + 3 * u, 11 * u, 3.2 * u, 0, 0, Math.PI * 2);
    ctx.fill();

    // NFC stand base.
    const baseG = ctx.createLinearGradient(cx - 11 * u, 0, cx + 11 * u, 0);
    baseG.addColorStop(0, pal.baseSide);
    baseG.addColorStop(0.5, pal.baseTop);
    baseG.addColorStop(1, pal.baseSide);
    ctx.fillStyle = baseG;
    ctx.beginPath();
    ctx.ellipse(cx, baseY, 11 * u, 4.6 * u, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = Math.max(1, 1.4 * u);
    ctx.strokeStyle = pal.baseEdge;
    ctx.stroke();
    ctx.fillStyle = isAlive ? "#101915" : "#20272d";
    ctx.beginPath();
    ctx.ellipse(cx, baseY - u, 7.5 * u, 2.8 * u, 0, 0, Math.PI * 2);
    ctx.fill();

    // Fallen figures lean; living ones stand straight.
    ctx.translate(cx, baseY);
    if (!isAlive) {
        ctx.rotate(-0.14);
    }
    ctx.translate(-cx, -baseY);

    // Feet.
    ctx.fillStyle = pal.bodyDark;
    ctx.beginPath();
    ctx.ellipse(cx - 3.4 * u, baseY - 2.6 * u, 2.4 * u, 1.6 * u, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(cx + 3.4 * u, baseY - 2.6 * u, 2.4 * u, 1.6 * u, 0, 0, Math.PI * 2);
    ctx.fill();

    // Body.
    const bodyG = ctx.createLinearGradient(0, baseY - 14 * u, 0, baseY - 2 * u);
    bodyG.addColorStop(0, pal.bodyLight);
    bodyG.addColorStop(0.55, pal.bodyMid);
    bodyG.addColorStop(1, pal.bodyDark);
    ctx.fillStyle = bodyG;
    ctx.beginPath();
    ctx.ellipse(cx, baseY - 8 * u, 5.2 * u, 6 * u, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = Math.max(1, u);
    ctx.strokeStyle = pal.bodyDark;
    ctx.stroke();

    // Belly patch.
    ctx.fillStyle = "rgba(255, 255, 255, 0.28)";
    ctx.beginPath();
    ctx.ellipse(cx, baseY - 7 * u, 2.6 * u, 3.4 * u, 0, 0, Math.PI * 2);
    ctx.fill();

    // Arms.
    ctx.fillStyle = pal.bodyMid;
    ctx.beginPath();
    ctx.ellipse(cx - 5.6 * u, baseY - 8 * u, 1.5 * u, 2.6 * u, 0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(cx + 5.6 * u, baseY - 8 * u, 1.5 * u, 2.6 * u, -0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Head.
    const headY = baseY - 16 * u;
    const headR = 6.6 * u;
    const headG = ctx.createLinearGradient(0, headY - headR, 0, headY + headR);
    headG.addColorStop(0, pal.headLight);
    headG.addColorStop(0.55, pal.headMid);
    headG.addColorStop(1, pal.headDark);
    ctx.fillStyle = headG;
    ctx.beginPath();
    ctx.arc(cx, headY, headR, 0, Math.PI * 2);
    ctx.fill();
    ctx.lineWidth = Math.max(1, 1.2 * u);
    ctx.strokeStyle = pal.headDark;
    ctx.stroke();

    // Sprout on top.
    ctx.strokeStyle = pal.leafDark;
    ctx.lineWidth = Math.max(1, u);
    ctx.beginPath();
    ctx.moveTo(cx, headY - headR + u);
    ctx.lineTo(cx + u, headY - headR - 2.4 * u);
    ctx.stroke();
    ctx.fillStyle = pal.leaf;
    ctx.beginPath();
    ctx.ellipse(cx - 1.6 * u, headY - headR - 2 * u, 2 * u, u, -0.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(cx + 2.4 * u, headY - headR - 3 * u, 2 * u, u, 0.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Face.
    const eyeY = headY - 0.5 * u;
    const eyeDX = 2.7 * u;
    const eyeR = 2.1 * u;

    if (isAlive) {
        for (const side of [-1, 1]) {
            const ex = cx + side * eyeDX;
            ctx.fillStyle = "#ffffff";
            ctx.beginPath();
            ctx.arc(ex, eyeY, eyeR, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#0b1510";
            ctx.beginPath();
            ctx.arc(ex + side * 0.4 * u, eyeY + 0.3 * u, 1.1 * u, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#ffffff";
            ctx.beginPath();
            ctx.arc(ex + side * 0.4 * u + 0.4 * u, eyeY - 0.2 * u, 0.45 * u, 0, Math.PI * 2);
            ctx.fill();
        }

        // Smile + blush.
        ctx.strokeStyle = "rgba(8, 20, 14, 0.65)";
        ctx.lineWidth = Math.max(1, 0.9 * u);
        ctx.beginPath();
        ctx.arc(cx, eyeY + 1.6 * u, 1.8 * u, 0.25 * Math.PI, 0.75 * Math.PI);
        ctx.stroke();
        ctx.fillStyle = pal.cheek;
        ctx.beginPath();
        ctx.arc(cx - 4.4 * u, eyeY + 1.8 * u, 1.2 * u, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(cx + 4.4 * u, eyeY + 1.8 * u, 1.2 * u, 0, Math.PI * 2);
        ctx.fill();
    } else {
        ctx.strokeStyle = "#b03030";
        ctx.lineWidth = Math.max(1.2, 1.5 * u);
        ctx.lineCap = "round";
        for (const side of [-1, 1]) {
            const ex = cx + side * eyeDX;
            const s = 1.5 * u;
            ctx.beginPath();
            ctx.moveTo(ex - s, eyeY - s);
            ctx.lineTo(ex + s, eyeY + s);
            ctx.moveTo(ex + s, eyeY - s);
            ctx.lineTo(ex - s, eyeY + s);
            ctx.stroke();
        }

        // Crack across the head.
        ctx.strokeStyle = "rgba(10, 14, 17, 0.9)";
        ctx.lineWidth = Math.max(1, u);
        ctx.beginPath();
        ctx.moveTo(cx - 5 * u, headY - 3 * u);
        ctx.lineTo(cx - 2 * u, headY - u);
        ctx.lineTo(cx - 3.4 * u, headY + 2.4 * u);
        ctx.stroke();
    }

    // Rim light + gloss (living only).
    if (isAlive) {
        ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
        ctx.lineWidth = Math.max(1, u);
        ctx.beginPath();
        ctx.arc(cx, headY, headR - u, -0.5, 0.5);
        ctx.stroke();
        ctx.fillStyle = "rgba(255, 255, 255, 0.35)";
        ctx.beginPath();
        ctx.ellipse(cx - 3 * u, headY - 3.4 * u, 1.8 * u, 1.1 * u, -0.6, 0, Math.PI * 2);
        ctx.fill();
    }

    // Selection: gold ring around the stand.
    if (isSelected) {
        ctx.globalAlpha = 1;
        ctx.save();
        ctx.shadowColor = "rgba(255, 215, 106, 0.9)";
        ctx.shadowBlur = 12;
        ctx.strokeStyle = "#ffd76a";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.ellipse(cx, baseY, 12.5 * u, 6 * u, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
    }

    ctx.restore();
}


/* =========================================
   RENDER STYLE REGISTRY + DISPATCH
   Python stays authoritative for state;
   this only switches the display bitmaps.
   ========================================= */

const RENDER_STYLE_STORAGE_KEY = "digital-life-sprite-style";
const DEFAULT_RENDER_STYLE = "pixel";

const RENDER_STYLES = {
    dots: {
        label: "Classic dots",
        description: "Original flat colored dots.",
        radiusOf: dotsOrganismRadius,
        drawFood: dotsDrawFood,
        drawOrganism: dotsDrawOrganism,
    },
    cells: {
        label: "Lab cells",
        description: "Glossy vector cells with pulse.",
        radiusOf: cellOrganismRadius,
        drawFood: cellDrawFood,
        drawOrganism: cellDrawOrganism,
    },
    pixel: {
        label: "Pixel followers",
        description: "Populous-style 16-bit bitmaps.",
        radiusOf: pixelOrganismRadius,
        drawFood: pixelDrawFood,
        drawOrganism: pixelDrawOrganism,
    },
    amiibo: {
        label: "Amiibo figures",
        description: "Realistic figurines on NFC stands.",
        radiusOf: amiiboOrganismRadius,
        drawFood: amiiboDrawFood,
        drawOrganism: amiiboDrawOrganism,
    },
};

let currentRenderStyle = loadRenderStyle();

function loadRenderStyle() {
    try {
        const saved = window.localStorage.getItem(RENDER_STYLE_STORAGE_KEY);

        if (saved && RENDER_STYLES[saved]) {
            return saved;
        }
    } catch {
        // Storage unavailable; fall through to default.
    }

    return DEFAULT_RENDER_STYLE;
}

function setRenderStyle(name) {
    if (!RENDER_STYLES[name]) {
        return false;
    }

    currentRenderStyle = name;

    try {
        window.localStorage.setItem(RENDER_STYLE_STORAGE_KEY, name);
    } catch {
        // Storage unavailable; style still applies for this session.
    }

    document.body.dataset.spriteStyle = name;
    syncSpriteSelect();

    if (latestState) {
        renderWorld();
    }

    return true;
}

function syncSpriteSelect() {
    const { spriteSelect } = getSettingsElements();

    if (spriteSelect && spriteSelect.value !== currentRenderStyle) {
        spriteSelect.value = currentRenderStyle;
    }

    const hint = document.getElementById("sprite-style-hint");

    if (hint) {
        hint.textContent = RENDER_STYLES[currentRenderStyle].description;
    }
}

function drawFood(foodItems) {
    return RENDER_STYLES[currentRenderStyle].drawFood(foodItems);
}

function getOrganismRadius(organism) {
    return RENDER_STYLES[currentRenderStyle].radiusOf(organism);
}

function drawOrganism(organism) {
    return RENDER_STYLES[currentRenderStyle].drawOrganism(organism);
}

function renderWorld() {
    if (!latestState) {
        return;
    }

    drawBackground();

    // Pixel-art bitmaps must stay crisp: smoothing stays on for
    // the other styles, off for hard pixel edges.
    ctx.imageSmoothingEnabled = currentRenderStyle !== "pixel";

    drawFood(latestState.food || []);

    /*
     * Draw dead organisms first so living organisms
     * remain easier to see when coordinates overlap.
     */

    const organisms = latestState.organisms || [];

    for (const organism of organisms) {
        const isAlive = organism.alive && organism.health > 0;

        if (!isAlive) {
            drawOrganism(organism);
        }
    }

    for (const organism of organisms) {
        const isAlive = organism.alive && organism.health > 0;

        if (isAlive) {
            drawOrganism(organism);
        }
    }
}


/* =========================================
   STATISTICS PANEL
   ========================================= */

function updateStatistics(state) {
    const statistics = state.statistics || {};

    setText("simulation-tick", formatInteger(state.tick));

    setText(
        "living-population",
        formatInteger(state.population)
    );

    setText(
        "total-organisms",
        formatInteger(state.total_organisms)
    );

    setText(
        "dead-population",
        formatInteger(statistics.dead_population)
    );

    setText(
        "food-remaining",
        formatInteger(state.food_remaining)
    );

    setText(
        "world-width",
        formatInteger(state.world.width)
    );

    setText(
        "world-height",
        formatInteger(state.world.height)
    );

    setText(
        "average-energy",
        formatNumber(statistics.average_energy)
    );

    setText(
        "average-health",
        formatNumber(statistics.average_health)
    );

    setText(
        "average-age",
        formatNumber(statistics.average_age)
    );

    setText(
        "average-metabolism",
        formatNumber(statistics.average_metabolism)
    );
}


/* =========================================
   ORGANISM INSPECTOR
   ========================================= */

function updateOrganismInspector() {
    const emptyPanel = document.getElementById("inspector-empty");
    const detailsPanel = document.getElementById("inspector-details");

    if (!latestState || selectedOrganismId === null) {
        emptyPanel.hidden = false;
        detailsPanel.hidden = true;

        setText("selected-organism-id", "No selection");

        return;
    }

    /*
     * The serializer currently exports organism IDs
     * using the "id" property.
     */

    const organism = latestState.organisms.find(
        item => item.id === selectedOrganismId
    );

    if (!organism) {
        selectedOrganismId = null;

        emptyPanel.hidden = false;
        detailsPanel.hidden = true;

        setText("selected-organism-id", "No selection");

        return;
    }

    emptyPanel.hidden = true;
    detailsPanel.hidden = false;

    setText(
        "selected-organism-id",
        `Organism #${organism.id}`
    );

    const isAlive = organism.alive && organism.health > 0;
    setText("organism-status", isAlive ? "Alive" : "Dead");

    if (Number.isFinite(Number(organism.x))
        && Number.isFinite(Number(organism.y))) {
        setText(
            "organism-position",
            `(${formatNumber(organism.x, 1)}, ${formatNumber(organism.y, 1)})`
        );
    } else {
        setText("organism-position", "—");
    }

    setText("organism-energy", formatNumber(organism.energy));
    setText("organism-health", formatNumber(organism.health));
    setText("organism-age", formatInteger(organism.age));

    setText(
        "organism-generation",
        formatInteger(organism.generation)
    );

    setText(
        "organism-parent",
        organism.parent_id ?? "None"
    );

    setText(
        "organism-offspring",
        formatInteger(organism.offspring_count)
    );

    const genome = organism.genome || {};

    setText("genome-speed", formatNumber(genome.speed));
    setText("genome-vision", formatNumber(genome.vision));
    setText("genome-metabolism", formatNumber(genome.metabolism));
    setText("genome-size", formatNumber(genome.size));

    setText(
        "genome-reproduction",
        formatNumber(genome.reproduction_threshold)
    );

    setText(
        "genome-mutation",
        formatNumber(genome.mutation_rate)
    );

    if (latestState && Number.isFinite(Number(latestState.tick))) {
        setText("inspector-tick", formatInteger(latestState.tick));
    } else {
        setText("inspector-tick", "—");
    }

    verifySelectedOrganism(organism.id);
}


/* =========================================
   ORGANISM DETAIL VERIFICATION
   Confirms the selection against the backend
   without treating cache as truth.
   ========================================= */

async function verifySelectedOrganism(organismId) {
    const errorElement = document.getElementById("inspector-error");

    try {
        const response = await fetch(
            `${ORGANISM_URL}/${organismId}`,
            { method: "GET", cache: "no-store" }
        );

        if (response.status === 404) {
            if (errorElement) {
                errorElement.textContent =
                    "This organism is no longer in the backend state. "
                    + "Shown values are from the last received snapshot.";
                errorElement.hidden = false;
            }

            return;
        }

        if (!response.ok) {
            throw new Error(`Organism API returned HTTP ${response.status}.`);
        }

        if (errorElement) {
            errorElement.textContent = "";
            errorElement.hidden = true;
        }
    } catch (error) {
        /* Best-effort only: snapshot data stays visible. */
        console.error("Failed to verify selected organism:", error);
    }
}


/* =========================================
   CANVAS INTERACTION
   ========================================= */

function findOrganismAtPoint(x, y) {
    if (!latestState) {
        return null;
    }

    /*
     * Search in reverse draw order so the organism
     * rendered on top is selected first.
     */

    const organisms = [...(latestState.organisms || [])].reverse();

    for (const organism of organisms) {
        if (
            !Number.isFinite(organism.x) ||
            !Number.isFinite(organism.y)
        ) {
            continue;
        }

        const radius = getOrganismRadius(organism) + 9;

        const dx = organism.x - x;
        const dy = organism.y - y;

        if (dx * dx + dy * dy <= radius * radius) {
            return organism;
        }
    }

    return null;
}

canvas.addEventListener("click", event => {
    if (!latestState) {
        return;
    }

    const rect = canvas.getBoundingClientRect();

    /*
     * Convert browser display coordinates to the
     * Python world's coordinate system.
     */

    const x = (event.clientX - rect.left)
        * (canvasWidth / rect.width);

    const y = (event.clientY - rect.top)
        * (canvasHeight / rect.height);

    const organism = findOrganismAtPoint(x, y);

    selectedOrganismId = organism ? organism.id : null;

    updateOrganismInspector();
    renderWorld();
});


/* =========================================
   API STATE VALIDATION
   ========================================= */

function validateState(state) {
    if (!state || typeof state !== "object") {
        throw new Error("The API returned an invalid response.");
    }

    if (
        !state.world ||
        !Number.isFinite(state.world.width) ||
        !Number.isFinite(state.world.height) ||
        state.world.width <= 0 ||
        state.world.height <= 0
    ) {
        throw new Error("The API returned invalid world dimensions.");
    }

    if (!Array.isArray(state.organisms)) {
        throw new Error("The API response has no organism array.");
    }

    if (!Array.isArray(state.food)) {
        throw new Error("The API response has no food array.");
    }

    return state;
}


/* =========================================
   SIMULATION SETTINGS (TICKS PER SECOND)
   ========================================= */

function getSettingsElements() {
    return {
        toggle: document.getElementById("settings-toggle"),
        panel: document.getElementById("settings-panel"),
        input: document.getElementById("ticks-per-second-input"),
        slider: document.getElementById("ticks-per-second-slider"),
        applyButton: document.getElementById("ticks-apply-button"),
        status: document.getElementById("settings-status"),
        spriteSelect: document.getElementById("sprite-style-select"),
    };
}

function setSettingsStatus(message, kind) {
    const { status } = getSettingsElements();

    if (!status) {
        return;
    }

    status.textContent = message || "";

    status.classList.toggle("success", kind === "success");
    status.classList.toggle("error", kind === "error");
}

function syncTicksInputs(value) {
    const { input, slider } = getSettingsElements();

    if (!Number.isFinite(value)) {
        return;
    }

    currentTicksPerSecond = value;

    if (input && document.activeElement !== input) {
        input.value = String(value);
    }

    if (slider) {
        slider.value = String(value);
    }
}

function setTicksControlsEnabled(enabled) {
    const { input, slider, applyButton } = getSettingsElements();

    if (input) {
        input.disabled = !enabled;
    }

    if (slider) {
        slider.disabled = !enabled;
    }

    if (applyButton) {
        applyButton.disabled = !enabled;
    }
}

async function fetchSimulationConfig() {
    try {
        const response = await fetch(CONFIG_URL, {
            method: "GET",
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error(`Config API returned HTTP ${response.status}.`);
        }

        const config = await response.json();

        if (Number.isFinite(Number(config.min_ticks_per_second))) {
            minTicksPerSecond = Number(config.min_ticks_per_second);
        }

        if (Number.isFinite(Number(config.max_ticks_per_second))) {
            maxTicksPerSecond = Number(config.max_ticks_per_second);
        }

        const { input, slider } = getSettingsElements();

        if (input) {
            input.min = String(minTicksPerSecond);
            input.max = String(maxTicksPerSecond);
        }

        if (slider) {
            slider.min = String(minTicksPerSecond);
            slider.max = String(maxTicksPerSecond);
        }

        if (Number.isFinite(Number(config.ticks_per_second))) {
            syncTicksInputs(Number(config.ticks_per_second));
        }

        setTicksControlsEnabled(true);
    } catch (error) {
        console.error("Failed to fetch simulation config:", error);
        setSettingsStatus("Could not load speed setting.", "error");
    }
}

async function applyTicksPerSecond(requestedValue) {
    const value = Number(requestedValue);

    if (!Number.isFinite(value)) {
        setSettingsStatus("Enter a valid number.", "error");
        return false;
    }

    if (value < minTicksPerSecond || value > maxTicksPerSecond) {
        setSettingsStatus(
            `Enter a value between ${minTicksPerSecond} and ${maxTicksPerSecond}.`,
            "error"
        );
        return false;
    }

    if (isApplyingTicks) {
        return false;
    }

    isApplyingTicks = true;
    setTicksControlsEnabled(false);
    setSettingsStatus("Applying...", "");

    try {
        const response = await fetch(CONFIG_URL, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticks_per_second: value }),
        });

        if (!response.ok) {
            let detail = `Config API returned HTTP ${response.status}.`;

            try {
                const errorBody = await response.json();

                if (typeof errorBody.detail === "string") {
                    detail = errorBody.detail;
                }
            } catch {
                // Keep the default HTTP status message.
            }

            throw new Error(detail);
        }

        const config = await response.json();

        syncTicksInputs(Number(config.ticks_per_second));
        setSettingsStatus(
            `Speed set to ${config.ticks_per_second} ticks/sec.`,
            "success"
        );

        return true;
    } catch (error) {
        console.error("Failed to update ticks per second:", error);
        setSettingsStatus(error.message || "Could not update speed.", "error");

        return false;
    } finally {
        isApplyingTicks = false;
        setTicksControlsEnabled(true);
    }
}

function initializeSettings() {
    const { toggle, panel, input, slider, applyButton, spriteSelect } = getSettingsElements();

    if (!toggle || !panel || !input || !slider || !applyButton || !spriteSelect) {
        return;
    }

    document.body.dataset.spriteStyle = currentRenderStyle;
    syncSpriteSelect();

    spriteSelect.addEventListener("change", () => {
        setRenderStyle(spriteSelect.value);
    });

    toggle.addEventListener("click", event => {
        event.stopPropagation();

        const isHidden = panel.hidden;

        panel.hidden = !isHidden;
        toggle.setAttribute("aria-expanded", String(isHidden));
    });

    document.addEventListener("click", event => {
        if (panel.hidden) {
            return;
        }

        if (!panel.contains(event.target) && !toggle.contains(event.target)) {
            panel.hidden = true;
            toggle.setAttribute("aria-expanded", "false");
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !panel.hidden) {
            panel.hidden = true;
            toggle.setAttribute("aria-expanded", "false");
            toggle.focus();
        }
    });

    slider.addEventListener("input", () => {
        input.value = slider.value;
    });

    slider.addEventListener("change", () => {
        applyTicksPerSecond(slider.value);
    });

    applyButton.addEventListener("click", () => {
        applyTicksPerSecond(input.value);
    });

    input.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            applyTicksPerSecond(input.value);
        }
    });

    fetchSimulationConfig();
}


/* =========================================
   ANALYTICS CHARTS (backend metrics only)
   No placeholder data: every point comes from
   GET /simulation/metrics/history.
   ========================================= */

const CHART_SERIES = {
    population: { color: "#55e6a5", label: "Living" },
    births: { color: "#55e6a5", label: "Births" },
    deaths: { color: "#ff7777", label: "Deaths" },
    energy: { color: "#f4c95d", label: "Energy" },
};

function setAnalyticsStatus(message) {
    const element = document.getElementById("analytics-status");

    if (element) {
        element.textContent = message || "";
    }
}

function drawLineChart(canvasId, history, extractors) {
    const canvas = document.getElementById(canvasId);

    if (!canvas) {
        return;
    }

    const width = canvas.clientWidth || 260;
    const height = 150;
    const pixelRatio = Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO);

    canvas.width = Math.round(width * pixelRatio);
    canvas.height = Math.round(height * pixelRatio);

    const g = canvas.getContext("2d");
    g.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    g.clearRect(0, 0, width, height);

    const padding = { left: 34, right: 8, top: 8, bottom: 18 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;

    const points = history
        .map((snapshot) => ({
            tick: Number(snapshot.tick),
            values: extractors.map((extract) => {
                const value = extract(snapshot);
                return Number.isFinite(Number(value)) ? Number(value) : null;
            }),
        }))
        .filter((point) => Number.isFinite(point.tick));

    if (points.length === 0) {
        g.fillStyle = "#607583";
        g.font = "11px sans-serif";
        g.fillText("No data yet", padding.left, height / 2);
        return 0;
    }

    let maxValue = 0;

    for (const point of points) {
        for (const value of point.values) {
            if (value !== null && value > maxValue) {
                maxValue = value;
            }
        }
    }

    if (maxValue <= 0) {
        maxValue = 1;
    }

    const minTick = points[0].tick;
    const maxTick = points[points.length - 1].tick;
    const tickSpan = Math.max(maxTick - minTick, 1);

    /* Axes. */
    g.strokeStyle = "rgba(130, 160, 175, 0.25)";
    g.lineWidth = 1;
    g.beginPath();
    g.moveTo(padding.left, padding.top);
    g.lineTo(padding.left, padding.top + plotHeight);
    g.lineTo(padding.left + plotWidth, padding.top + plotHeight);
    g.stroke();

    /* Y max + x tick labels. */
    g.fillStyle = "#607583";
    g.font = "10px sans-serif";
    g.fillText(formatNumber(maxValue, 1), 2, padding.top + 9);
    g.fillText(formatInteger(minTick), padding.left, height - 4);
    g.fillText(
        formatInteger(maxTick),
        padding.left + plotWidth - 28,
        height - 4
    );

    extractors.forEach((extract, seriesIndex) => {
        const color = (CHART_SERIES[extract.key] || {}).color || "#55e6a5";

        g.strokeStyle = color;
        g.lineWidth = 1.6;
        g.beginPath();

        let started = false;

        for (const point of points) {
            const value = point.values[seriesIndex];

            if (value === null) {
                started = false;
                continue;
            }

            const x = padding.left
                + ((point.tick - minTick) / tickSpan) * plotWidth;
            const y = padding.top + plotHeight
                - (value / maxValue) * plotHeight;

            if (!started) {
                g.moveTo(x, y);
                started = true;
            } else {
                g.lineTo(x, y);
            }
        }

        g.stroke();
    });

    return points.length;
}

function chartExtractor(key) {
    return Object.assign(
        (snapshot) => snapshot[key],
        { key }
    );
}

async function fetchMetricsHistory() {
    if (isHistoryFetching) {
        return;
    }

    isHistoryFetching = true;

    try {
        const response = await fetch(HISTORY_URL, {
            method: "GET",
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error(`Metrics API returned HTTP ${response.status}.`);
        }

        const body = await response.json();
        const history = Array.isArray(body.history) ? body.history : [];

        if (history.length === 0) {
            setAnalyticsStatus("No metrics recorded yet.");
            return;
        }

        const traitSelect = document.getElementById("trait-select");
        const traitKey = traitSelect ? traitSelect.value : "average_metabolism";
        const traitOption = traitSelect
            ? traitSelect.options[traitSelect.selectedIndex]
            : null;

        const caption = document.getElementById("trait-chart-caption");

        if (caption && traitOption) {
            caption.textContent = `${traitOption.text} (per tick)`;
        }

        const drawn = [
            drawLineChart("chart-population", history, [
                chartExtractor("living_population"),
            ]),
            drawLineChart("chart-vitality", history, [
                chartExtractor("births"),
                chartExtractor("deaths"),
            ]),
            drawLineChart("chart-energy", history, [
                chartExtractor("average_energy"),
            ]),
            drawLineChart("chart-trait", history, [
                chartExtractor(traitKey),
            ]),
        ];

        const lastTick = history[history.length - 1].tick;
        lastHistoryTick = lastTick;

        setAnalyticsStatus(
            `Showing ${drawn[0]} recorded tick(s), through tick ${lastTick}.`
        );
    } catch (error) {
        console.error("Failed to fetch metrics history:", error);
        setAnalyticsStatus("Metrics are temporarily unavailable.");
    } finally {
        isHistoryFetching = false;
    }
}


/* =========================================
   FETCH SIMULATION STATE
   ========================================= */

async function fetchSimulationState() {
    /*
     * Prevent overlapping requests if one request
     * takes longer than the polling interval.
     */

    if (isFetching) {
        return;
    }

    isFetching = true;
    const requestId = ++stateRequestId;

    try {
        const response = await fetch(API_URL, {
            method: "GET",
            cache: "no-store"
        });

        let payload;

        try {
            payload = await response.json();
        } catch {
            throw new Error("The API returned malformed data.");
        }

        if (!response.ok) {
            throw new Error(`API returned HTTP ${response.status}.`);
        }

        const state = validateState(payload);

        /* Ignore stale responses that arrive out of order. */
        if (requestId < lastAppliedRequestId) {
            return;
        }

        lastAppliedRequestId = requestId;
        latestState = state;
        consecutiveFailures = 0;

        const paused = state.paused === true;
        const simStatus = state.simulation_status;

        if (paused || simStatus === "paused") {
            setConnectionStatus(true, "Backend connected · Paused");
        } else {
            setConnectionStatus(true, "Backend connected");
        }

        hideLoadingMessage();
        markDataFreshness(false);

        updateStatistics(state);
        updateStatusPanel({
            simulation_status: simStatus,
            paused,
            ticks_per_second: state.ticks_per_second,
            living_population: state.population,
            total_organisms: state.total_organisms,
            last_tick: state.tick,
            worker_alive: lastBackendStatus
                ? lastBackendStatus.worker_alive
                : undefined,
            last_error: lastBackendStatus
                ? lastBackendStatus.last_error
                : undefined,
        });

        /*
         * Keep the settings inputs in sync if the backend
         * reports a ticks-per-second value (e.g. changed
         * in another tab), without clobbering active edits.
         */

        if (Number.isFinite(Number(state.ticks_per_second))) {
            const reported = Number(state.ticks_per_second);

            if (reported !== currentTicksPerSecond && !isApplyingTicks) {
                syncTicksInputs(reported);
            }
        }

        /*
         * The world dimensions come from the API.
         * The canvas adapts if those dimensions change.
         */

        const dimensionsChanged =
            canvasWidth !== state.world.width ||
            canvasHeight !== state.world.height;

        if (!hasInitializedCanvas || dimensionsChanged) {
            resizeCanvas();
            hasInitializedCanvas = true;
        } else {
            renderWorld();
        }

        updateOrganismInspector();

        /* Charts refresh on a slower cadence than state polling. */
        statePollCount += 1;

        if (statePollCount % 5 === 0 || lastHistoryTick === null) {
            fetchMetricsHistory();
        }

    } catch (error) {
        consecutiveFailures += 1;

        console.error("Failed to fetch simulation state:", error);

        if (!latestState) {
            setConnectionStatus(false, "Backend disconnected");
            setLoadingMessage(
                "Cannot connect to Digital Life. Start the FastAPI server and retry."
            );
        } else {
            /* Paused is a backend state, not a connection failure. */
            const wasPaused = lastBackendStatus
                && lastBackendStatus.paused === true;

            setConnectionStatus(
                false,
                wasPaused
                    ? "Backend unreachable · Paused"
                    : "Backend disconnected · Showing last state"
            );

            if (consecutiveFailures >= 3) {
                setLoadingMessage(
                    "Connection lost. Showing the last successfully received state."
                );
            }

            markDataFreshness(true);
        }

    } finally {
        isFetching = false;
    }
}


/* =========================================
   STARTUP
   ========================================= */

function startDashboard() {
    setConnectionStatus(false, "Connecting to simulation");

    setLoadingMessage("Connecting to the Python simulation...");

    initializeSettings();
    initializeControls();

    const traitSelect = document.getElementById("trait-select");

    if (traitSelect) {
        traitSelect.addEventListener("change", () => {
            fetchMetricsHistory();
        });
    }

    /*
     * Fetch immediately, then periodically refresh
     * the displayed state.
     *
     * Polling does not advance the simulation.
     * Status polling runs on a slower independent cadence.
     */

    fetchSimulationState();
    fetchSimulationStatus();
    fetchMetricsHistory();

    window.setInterval(
        fetchSimulationState,
        POLL_INTERVAL_MS
    );

    window.setInterval(
        fetchSimulationStatus,
        POLL_INTERVAL_MS * 5
    );

    window.addEventListener("resize", () => {
        if (latestState) {
            resizeCanvas();
            fetchMetricsHistory();
        }
    });
}

startDashboard();