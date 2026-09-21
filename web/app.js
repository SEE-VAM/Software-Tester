// Telemetry Client & UI Controller for AutoQA Robot

let eventSource = null;
const targetUrlInput = document.getElementById("target-url");
const headlessCheckbox = document.getElementById("headless-mode");

const btnStart = document.getElementById("btn-start");
const btnPause = document.getElementById("btn-pause");
const btnStop = document.getElementById("btn-stop");

const liveBadge = document.getElementById("live-badge");
const testStatusText = document.getElementById("test-status-text");

const statTotal = document.getElementById("stat-total");
const statPassed = document.getElementById("stat-passed");
const statFailed = document.getElementById("stat-failed");

const moduleList = document.getElementById("module-list");
const screensCount = document.getElementById("screens-count");
const logBox = document.getElementById("log-box");

const bugList = document.getElementById("bug-list");
const bugBadge = document.getElementById("bug-badge");
const noBugsMsg = document.getElementById("no-bugs-msg");

const currentScreenLabel = document.getElementById("current-screen-label");
const liveIframe = document.getElementById("live-iframe");
const idleScreenMsg = document.getElementById("idle-screen-msg");

// Connect SSE stream
function connectSSE() {
  if (eventSource) {
    eventSource.close();
  }

  eventSource = new EventSource("/api/events");

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleIncomingEvent(data);
    } catch (e) {
      console.error("SSE parse error:", e);
    }
  };

  eventSource.onerror = () => {
    console.warn("SSE connection disconnected, retrying in 3s...");
    setTimeout(connectSSE, 3000);
  };
}

function handleIncomingEvent(data) {
  switch (data.type) {
    case "init":
      if (data.state) {
        if (data.state.metrics) updateMetrics(data.state.metrics);
        if (data.state.is_running) setRunningState(true);
        if (data.state.screens) {
          Object.keys(data.state.screens).forEach(screen => {
            updateScreenModule(screen, data.state.screens[screen]);
          });
        }
        if (data.state.scenarios) {
          Object.keys(data.state.scenarios).forEach(sc => {
            updateScenarioBadge(sc, data.state.scenarios[sc].status, data.state.scenarios[sc].details);
          });
        }
        if (data.state.bugs) {
          data.state.bugs.forEach(bug => addBugCard(bug));
        }
        if (data.state.logs) {
          data.state.logs.forEach(log => appendLog(log.timestamp, log.message, log.status));
        }
      }
      break;

    case "status_changed":
      if (data.status === "running") {
        setRunningState(true);
      } else {
        setRunningState(false, data.status);
      }
      break;

    case "scenario_updated":
      updateScenarioBadge(data.name, data.status, data.details);
      break;

    case "metrics":
      updateMetrics(data);
      break;

    case "log":
      appendLog(data.timestamp, data.message, data.status);
      break;

    case "screen_changed":
      updateScreenModule(data.screen, data.status);
      currentScreenLabel.innerText = `Target Viewport: ${data.screen}`;
      break;

    case "bug_found":
      addBugCard(data.bug);
      break;

    case "run_completed":
      setRunningState(false, "Completed");
      appendLog(new Date().toLocaleTimeString(), "🎉 AutoQA Suite completed. All screens scanned.", "success");
      break;
  }
}

function updateMetrics(metrics) {
  statTotal.innerText = metrics.total || 0;
  statPassed.innerText = metrics.passed || 0;
  statFailed.innerText = metrics.failed || 0;
}

function appendLog(time, message, status = "info") {
  const item = document.createElement("div");
  item.className = "log-item";

  let statusClass = "";
  if (status === "success") statusClass = "log-success";
  if (status === "error") statusClass = "log-error";

  item.innerHTML = `<span class="log-time">[${time}]</span> <span class="${statusClass}">${escapeHtml(message)}</span>`;
  logBox.appendChild(item);
  logBox.scrollTop = logBox.scrollHeight;
}

const discoveredScreens = new Map();

function updateScreenModule(screenName, status) {
  if (!screenName) return;

  const placeholder = document.querySelector(".module-placeholder");
  if (placeholder) placeholder.remove();

  let el = discoveredScreens.get(screenName);
  if (!el) {
    el = document.createElement("li");
    el.className = "module-item";
    moduleList.appendChild(el);
    discoveredScreens.set(screenName, el);
    screensCount.innerText = discoveredScreens.size;
  }

  let tagClass = "tag-pending";
  let statusText = status.toUpperCase();

  if (status.toLowerCase() === "passed") tagClass = "tag-passed";
  if (status.toLowerCase() === "testing") tagClass = "tag-progress";
  if (status.toLowerCase() === "failed") tagClass = "tag-failed";

  el.innerHTML = `
    <span>${escapeHtml(screenName)}</span>
    <span class="tag ${tagClass}">${statusText}</span>
  `;
}

let bugsCount = 0;
function addBugCard(bug) {
  if (!bug) return;
  if (noBugsMsg) noBugsMsg.style.display = "none";

  bugsCount++;
  bugBadge.innerText = bugsCount;

  const card = document.createElement("div");
  card.className = "bug-card";

  const shotHtml = bug.screenshot
    ? `<a href="/screenshots/${bug.screenshot}" target="_blank"><img class="bug-thumb" src="/screenshots/${bug.screenshot}" alt="Failure Screenshot" /></a>`
    : "";

  card.innerHTML = `
    <div class="bug-title">⚠️ ${escapeHtml(bug.title)}</div>
    <div class="bug-selector">Selector: <code>${escapeHtml(bug.selector)}</code></div>
    <div class="bug-error-text">${escapeHtml(bug.error)}</div>
    ${shotHtml}
  `;

  bugList.prepend(card);
}

function setRunningState(isRunning, finalStatus = "idle") {
  btnStart.disabled = isRunning;
  btnPause.disabled = !isRunning;
  btnStop.disabled = !isRunning;

  if (isRunning) {
    liveBadge.className = "status-badge running";
    testStatusText.innerText = "LIVE: Testing in Progress";
    const targetUrl = targetUrlInput.value.trim();
    if (targetUrl.startsWith("file://") || targetUrl.includes(":\\") || targetUrl.includes(":/")) {
      liveIframe.style.display = "none";
      idleScreenMsg.style.display = "block";
      idleScreenMsg.innerHTML = `
        <div style="font-size: 40px; margin-bottom: 8px;">📂</div>
        <h3 style="color:#f1f5f9; font-size:15px; margin-bottom:4px;">Local Offline File Testing</h3>
        <p style="font-size:12px; color:#94a3b8;">Testing local file directly. Check <strong>"Visible Browser"</strong> to watch the automation live in Chromium!</p>
      `;
    } else {
      idleScreenMsg.style.display = "none";
      liveIframe.style.display = "block";
      liveIframe.src = targetUrl;
    }
  } else {
    liveBadge.className = "status-badge idle";
    testStatusText.innerText = finalStatus === "Completed" ? "Completed (Ready)" : "Idle";
    btnPause.innerText = "⏸ Pause";
  }
}

function updateScenarioBadge(name, status, details) {
  let tagId = null;
  const n = (name || "").toLowerCase();
  if (n.includes("bill") || n.includes("checkout")) tagId = "tag-billing";
  else if (n.includes("product")) tagId = "tag-product";
  else if (n.includes("customer")) tagId = "tag-customer";
  else if (n.includes("hold")) tagId = "tag-hold";

  if (!tagId) return;
  const tagEl = document.getElementById(tagId);
  if (!tagEl) return;

  tagEl.innerText = status.toUpperCase();
  tagEl.className = "tag";

  const s = (status || "").toLowerCase();
  if (s === "passed") tagEl.classList.add("tag-passed");
  else if (s === "testing") tagEl.classList.add("tag-progress");
  else if (s === "failed") tagEl.classList.add("tag-failed");
  else tagEl.classList.add("tag-pending");
}

function resetScenarioBadges() {
  ["tag-billing", "tag-product", "tag-customer", "tag-hold"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.innerText = "QUEUED";
      el.className = "tag tag-pending";
    }
  });
}

// User Actions
async function startTestSuite() {
  const url = targetUrlInput.value.trim() || "http://localhost:8080";
  const visible = headlessCheckbox.checked;

  resetScenarioBadges();

  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_url: url, headless: !visible })
    });
    const data = await res.json();
    if (res.ok) {
      appendLog(new Date().toLocaleTimeString(), data.message, "info");
      setRunningState(true);
    } else {
      alert("Could not start test: " + data.error);
    }
  } catch (err) {
    alert("Backend error: " + err.message);
  }
}

async function pauseTestSuite() {
  try {
    const res = await fetch("/api/pause", { method: "POST" });
    const data = await res.json();
    btnPause.innerText = data.is_paused ? "▶ Resume" : "⏸ Pause";
  } catch (err) {
    console.error("Pause error:", err);
  }
}

async function stopTestSuite() {
  try {
    await fetch("/api/stop", { method: "POST" });
    setRunningState(false, "Stopped");
  } catch (err) {
    console.error("Stop error:", err);
  }
}

function exportReport() {
  window.open("/api/export-report", "_blank");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Initialize on page load
window.addEventListener("DOMContentLoaded", () => {
  connectSSE();
});
