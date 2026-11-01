/* ============================================================
   AI-NIDS DASHBOARD JAVASCRIPT
   ============================================================ */

/* LIVE CLOCK */
function updateClock() {
    const timeElement = document.getElementById("live-time");
    const dateElement = document.getElementById("live-date");

    if (!timeElement || !dateElement) return;

    const now = new Date();

    timeElement.textContent = now.toLocaleTimeString("en-IN", {
        hour12: false
    });

    dateElement.textContent = now.toLocaleDateString("en-IN", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric"
    });
}

/* SYSTEM HEALTH */
async function updateSystemStatus() {
    const statusElement = document.getElementById("status");
    if (!statusElement) return;

    try {
        const response = await fetch("/health?ts=" + Date.now(), {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Health endpoint returned HTTP " + response.status);
        }

        const data = await response.json();

        if (data.status !== "running") {
            throw new Error("Unexpected health status");
        }

        statusElement.textContent = "● SYSTEM ONLINE";
        statusElement.classList.remove("system-offline");
        statusElement.classList.add("system-online");
    } catch (error) {
        console.error("AI-NIDS health check error:", error);
        statusElement.textContent = "● SYSTEM OFFLINE";
        statusElement.classList.remove("system-online");
        statusElement.classList.add("system-offline");
    }
}

/* ESCAPE HTML */
function escapeHtml(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* FORMAT BYTES */
function formatBytes(bytes) {
    const number = Number(bytes) || 0;

    if (number < 1024) return number + " B";
    if (number < 1024 * 1024) return (number / 1024).toFixed(2) + " KB";
    if (number < 1024 * 1024 * 1024) {
        return (number / (1024 * 1024)).toFixed(2) + " MB";
    }

    return (number / (1024 * 1024 * 1024)).toFixed(2) + " GB";
}

/* STATUS CLASS */
function getStatusClass(status) {
    const normalized = String(status || "").trim().toUpperCase();

    if (normalized === "ATTACK") return "status-cell-attack";
    if (normalized === "SUSPICIOUS") return "status-cell-suspicious";

    return "status-cell-normal";
}

/* LOAD RECENT DETECTIONS AND SUMMARY COUNTS */
async function loadDetections() {
    try {
        const response = await fetch("/detections?ts=" + Date.now(), {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Detection API returned HTTP " + response.status);
        }

        const data = await response.json();

        const normalCount = document.getElementById("normal-count");
        const suspiciousCount = document.getElementById("suspicious-count");
        const attackCount = document.getElementById("attack-count");

        if (normalCount) {
            normalCount.textContent = String(Number(data.normal) || 0);
        }

        if (suspiciousCount) {
            suspiciousCount.textContent = String(Number(data.suspicious) || 0);
        }

        if (attackCount) {
            attackCount.textContent = String(Number(data.attacks) || 0);
        }

        const detectionsElement = document.getElementById("detections");
        if (!detectionsElement) return;

        const detections = Array.isArray(data.detections)
            ? data.detections
            : [];

        if (detections.length === 0) {
            detectionsElement.innerHTML =
                '<tr><td colspan="5">No detections recorded yet.</td></tr>';
            return;
        }

        detectionsElement.innerHTML = detections.map(detection => {
            const status = String(detection.status || "NORMAL")
                .trim()
                .toUpperCase();

            const attackClass = detection.attack_class
                ? escapeHtml(detection.attack_class)
                : "—";

            return `
                <tr>
                    <td>${escapeHtml(detection.time)}</td>
                    <td>${escapeHtml(detection.source_ip)}</td>
                    <td>${escapeHtml(detection.destination_ip)}</td>
                    <td>
                        <span class="${getStatusClass(status)}">
                            ${escapeHtml(status)}
                        </span>
                    </td>
                    <td>${attackClass}</td>
                </tr>
            `;
        }).join("");
    } catch (error) {
        console.error("Could not load detections:", error);
    }
}

/* CURRENT DETECTION */
async function updateCurrentDetection() {
    const container = document.getElementById("attack-details");
    const card = document.getElementById("detection-card");

    if (!container) return;

    try {
        const response = await fetch("/detections?ts=" + Date.now(), {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Could not load detection data");
        }

        const data = await response.json();

        const detections = Array.isArray(data.detections)
            ? data.detections
            : [];

        const latestAttack = detections.find(detection =>
            String(detection.status || "").trim().toUpperCase() === "ATTACK"
        );

        if (latestAttack) {
            if (card) {
                card.classList.add("detection-attack");
                card.classList.remove("detection-normal");
            }

            container.innerHTML = `
                <div class="detection-status status-attack">
                    🔴 AI ATTACK CLASSIFICATION
                </div>
                <p class="subtitle attack-warning">
                    This network flow was classified as potentially malicious.
                    Investigation is recommended.
                </p>
                <div class="detail-grid">
                    <div class="detail">
                        <span class="detail-label">Attack Class</span>
                        <span class="detail-value attack-class">
                            ${escapeHtml(latestAttack.attack_class || "Unknown")}
                        </span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">Detection Time</span>
                        <span class="detail-value">
                            ${escapeHtml(latestAttack.time)}
                        </span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">Source IP</span>
                        <span class="detail-value">
                            ${escapeHtml(latestAttack.source_ip)}
                        </span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">Destination IP</span>
                        <span class="detail-value">
                            ${escapeHtml(latestAttack.destination_ip)}
                        </span>
                    </div>
                </div>
            `;
        } else {
            if (card) {
                card.classList.remove("detection-attack");
                card.classList.add("detection-normal");
            }

            container.innerHTML = `
                <div class="detection-status status-normal">
                    ● NETWORK SECURE
                </div>
                <p class="subtitle">
                    No recent attack classifications.
                    Network traffic is being monitored.
                </p>
            `;
        }
    } catch (error) {
        console.error("Could not update current detection:", error);
    }
}

/* SHAP EXPLANATION - EXISTING DASHBOARD FEATURE */
async function updateShapExplanation() {
    const container = document.getElementById("shap-explanation");
    if (!container) return;

    try {
        const response = await fetch("/shap?ts=" + Date.now(), {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("SHAP API error");
        }

        const data = await response.json();

        if (!data.available ||
            !Array.isArray(data.features) ||
            data.features.length === 0) {
            container.innerHTML = `
                <div class="shap-empty">
                    <div class="shap-empty-icon">🧠</div>
                    <p>No AI explanation available</p>
                    <span>SHAP results appear after an attack classification.</span>
                </div>
            `;
            return;
        }

        const attackClass = data.attack_class || "Potential Attack";

        const rows = data.features.map(item => {
            const feature = item.feature || "Unknown";
            const importance = Number(item.importance) || 0;

            return `
                <li>
                    <span class="shap-feature">${escapeHtml(feature)}</span>
                    <span class="shap-value">${importance.toFixed(4)}</span>
                </li>
            `;
        }).join("");

        container.innerHTML = `
            <div class="shap-heading">
                <p class="subtitle">
                    Features influencing ${escapeHtml(attackClass)}
                </p>
            </div>
            <ul class="shap-list">${rows}</ul>
            <div class="shap-note">
                Higher absolute SHAP values indicate stronger influence
                on the model prediction.
            </div>
        `;
    } catch (error) {
        console.error("Could not load SHAP explanation:", error);
    }
}

/* LIVE NETWORK ACTIVITY */
async function updateLiveFlows() {
    const tableBody = document.getElementById("live-network-activity");
    if (!tableBody) return;

    try {
        const response = await fetch("/live-flows?ts=" + Date.now(), {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Live flow API error");
        }

        const data = await response.json();
        const flows = Array.isArray(data.flows) ? data.flows : [];

        if (flows.length === 0) {
            tableBody.innerHTML =
                '<tr><td colspan="8">Waiting for network traffic...</td></tr>';
            return;
        }

        tableBody.innerHTML = flows.map(flow => {
            const status = String(flow.status || "NORMAL")
                .trim()
                .toUpperCase();

            return `
                <tr>
                    <td>${escapeHtml(flow.time)}</td>
                    <td>${escapeHtml(flow.source_ip)}</td>
                    <td>${escapeHtml(flow.destination_ip)}</td>
                    <td>${escapeHtml(flow.dst_port)}</td>
                    <td>${escapeHtml(flow.protocol)}</td>
                    <td>${escapeHtml(flow.packet_count)}</td>
                    <td>${formatBytes(flow.total_bytes)}</td>
                    <td>
                        <span class="${getStatusClass(status)}">
                            ${escapeHtml(status)}
                        </span>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (error) {
        console.error("Could not load live flows:", error);
    }
}

/* ============================================================
   ATTACK HISTORY
   ============================================================ */

let attackHistoryRecords = [];
let attackHistoryIsOpen = false;
let attackHistoryRequestInProgress = false;

async function loadAttackHistory() {
    const rows = document.getElementById("attack-history-rows");
    const total = document.getElementById("attack-history-total");
    const updated = document.getElementById("attack-history-updated");

    if (!rows || attackHistoryRequestInProgress) return;

    attackHistoryRequestInProgress = true;

    try {
        const response = await fetch("/attack-history?ts=" + Date.now(), {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Attack history API returned HTTP " + response.status);
        }

        const data = await response.json();

        attackHistoryRecords = Array.isArray(data.attacks)
            ? data.attacks
            : [];

        if (total) {
            total.textContent = String(
                data.total ?? attackHistoryRecords.length
            );
        }

        renderAttackHistory();

        if (updated) {
            updated.textContent =
                "Last updated: " +
                new Date().toLocaleTimeString("en-IN", { hour12: false });
        }
    } catch (error) {
        console.error("Could not load attack history:", error);

        if (updated) {
            updated.textContent =
                "Unable to load history. Check the Flask server and API.";
        }

        if (attackHistoryRecords.length === 0) {
            rows.innerHTML =
                '<tr><td colspan="5">Could not load attack history.</td></tr>';
        }
    } finally {
        attackHistoryRequestInProgress = false;
    }
}

function renderAttackHistory() {
    const rows = document.getElementById("attack-history-rows");
    const search = document.getElementById("attack-history-search");

    if (!rows) return;

    const query = (search?.value || "").trim().toLowerCase();

    const filteredRecords = attackHistoryRecords.filter(record => {
        const searchableText = [
            record.time,
            record.source_ip,
            record.destination_ip,
            record.attack_class,
            record.status
        ].join(" ").toLowerCase();

        return searchableText.includes(query);
    });

    if (filteredRecords.length === 0) {
        rows.innerHTML =
            '<tr><td colspan="5">No matching attack records found.</td></tr>';
        return;
    }

    rows.innerHTML = filteredRecords.map(record => `
        <tr>
            <td>${escapeHtml(record.time || "—")}</td>
            <td>${escapeHtml(record.source_ip || "—")}</td>
            <td>${escapeHtml(record.destination_ip || "—")}</td>
            <td>${escapeHtml(record.attack_class || "Unknown")}</td>
            <td>
                <span class="${getStatusClass(record.status || "ATTACK")}">
                    ${escapeHtml(record.status || "ATTACK")}
                </span>
            </td>
        </tr>
    `).join("");
}

function openAttackHistory() {
    const modal = document.getElementById("attack-history-modal");
    if (!modal) return;

    modal.hidden = false;
    attackHistoryIsOpen = true;

    loadAttackHistory();

    document.getElementById("close-attack-history")?.focus();
}

function closeAttackHistory() {
    const modal = document.getElementById("attack-history-modal");
    if (!modal) return;

    modal.hidden = true;
    attackHistoryIsOpen = false;

    document.getElementById("attack-classifications-card")?.focus();
}

function initializeAttackHistory() {
    const card = document.getElementById("attack-classifications-card");
    const closeButton = document.getElementById("close-attack-history");
    const search = document.getElementById("attack-history-search");
    const modal = document.getElementById("attack-history-modal");

    card?.addEventListener("click", openAttackHistory);

    card?.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openAttackHistory();
        }
    });

    closeButton?.addEventListener("click", closeAttackHistory);
    search?.addEventListener("input", renderAttackHistory);

    modal?.addEventListener("click", event => {
        if (event.target === modal) {
            closeAttackHistory();
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && attackHistoryIsOpen) {
            closeAttackHistory();
        }
    });

    // Refresh attack history every five seconds while it is open.
    setInterval(() => {
        if (attackHistoryIsOpen) {
            loadAttackHistory();
        }
    }, 5000);
}

/* INITIALIZATION */
document.addEventListener("DOMContentLoaded", function () {
    updateClock();
    updateSystemStatus();
    loadDetections();
    updateCurrentDetection();
    updateShapExplanation();
    updateLiveFlows();
    initializeAttackHistory();

    setInterval(updateClock, 1000);
    setInterval(updateSystemStatus, 5000);
    setInterval(loadDetections, 3000);
    setInterval(updateCurrentDetection, 3000);
    setInterval(updateShapExplanation, 3000);
    setInterval(updateLiveFlows, 2000);
});