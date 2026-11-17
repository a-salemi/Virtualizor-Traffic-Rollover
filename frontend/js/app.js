/**
 * VirtuRoll Frontend Application Engine
 * Pure Vanilla JS, Dynamic Island Notifications, Responsive Mobile Cards
 */

let allVpsData = [];
let currentTab = "dashboard";

// --- Theme Management (Obsidian Dark & Apple Clean Light) ---
function initTheme() {
    const savedTheme = localStorage.getItem("virturoll_theme");
    let theme = savedTheme;
    
    if (!theme) {
        // Auto-detect system preference (default dark unless system explicitly prefers light)
        const prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
        theme = prefersLight ? "light" : "dark";
    }

    applyTheme(theme);
}

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("virturoll_theme", theme);
    
    const themeLabel = document.getElementById("themeLabel");
    if (themeLabel) {
        themeLabel.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const nextTheme = current === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
}

// --- Dynamic Island Notification System ---
function showToast(message, type = "info", duration = 3800) {
    const container = document.getElementById("dynamicIsland");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "dynamic-island-toast";

    let iconSvg = "";
    if (type === "success") {
        iconSvg = `<div class="toast-icon success"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg></div>`;
    } else if (type === "error") {
        iconSvg = `<div class="toast-icon error"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></div>`;
    } else {
        iconSvg = `<div class="toast-icon info"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg></div>`;
    }

    toast.innerHTML = `
        ${iconSvg}
        <div class="toast-text">${message}</div>
        <div class="toast-progress" style="transition: width ${duration}ms linear;"></div>
    `;

    container.appendChild(toast);

    // Trigger spring entry animation
    requestAnimationFrame(() => {
        toast.classList.add("active");
        const prog = toast.querySelector(".toast-progress");
        if (prog) {
            requestAnimationFrame(() => prog.style.width = "0%");
        }
    });

    // Auto-dismiss
    setTimeout(() => {
        toast.classList.remove("active");
        toast.classList.add("exit");
        setTimeout(() => toast.remove(), 400);
    }, duration);
}

// --- Authentication & Session ---
async function checkAuth() {
    try {
        const res = await fetch("/api/auth/me");
        if (res.ok) {
            document.getElementById("authView").style.display = "none";
            loadDashboard();
        } else {
            document.getElementById("authView").style.display = "flex";
        }
    } catch (e) {
        document.getElementById("authView").style.display = "flex";
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const u = document.getElementById("loginUsername").value;
    const p = document.getElementById("loginPassword").value;

    try {
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById("authView").style.display = "none";
            showToast(t("toast_login_success"), "success");
            loadDashboard();
        } else {
            showToast(data.detail || t("login_err"), "error");
        }
    } catch (err) {
        showToast(t("login_err"), "error");
    }
}

async function handleLogout() {
    try {
        await fetch("/api/auth/logout", { method: "POST" });
    } catch(e) {}
    showToast(t("toast_logout"), "info");
    document.getElementById("authView").style.display = "flex";
}

// --- Dashboard & VPS Rendering ---
async function loadDashboard() {
    try {
        // 1. Fetch system status
        const statusRes = await fetch("/api/system/status");
        if (statusRes.ok) {
            const stats = await statusRes.json();
            document.getElementById("statTotalVps").textContent = stats.total_vps;
            document.getElementById("statManagedBw").textContent = stats.total_managed_bw_gb;
            document.getElementById("statUsedBw").textContent = stats.total_used_bw_gb;
            document.getElementById("statRemainingBw").textContent = stats.total_remaining_bw_gb;
        }

        // 2. Fetch VPS list
        const vpsRes = await fetch("/api/vps");
        if (vpsRes.ok) {
            const data = await vpsRes.json();
            allVpsData = data.vps || [];
            renderVPS(allVpsData);
        }
    } catch (e) {
        console.error("Dashboard load error", e);
    }
}

function renderVPS(list) {
    const tbody = document.getElementById("vpsTableBody");
    tbody.innerHTML = "";

    if (!list || list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 30px;">No VPS records found. Click "Sync Virtualizor" to discover active nodes.</td></tr>`;
        return;
    }

    list.forEach(vps => {
        const tr = document.createElement("tr");

        const progressPercent = Math.min(100, Math.max(0, vps.used_percentage || 0));
        let progressColor = "var(--gradient-brand)";
        if (progressPercent > 85) progressColor = "var(--accent-rose)";
        else if (progressPercent > 65) progressColor = "var(--accent-amber)";

        tr.innerHTML = `
            <td data-label="${t('th_vpsid')}"><span class="badge-tag num-mono">#${vps.vpsid}</span></td>
            <td data-label="${t('th_hostname')}">
                <div style="font-weight: 600;">${vps.hostname}</div>
                <div class="num-mono" style="font-size: 0.78rem; color: var(--text-muted);">${vps.ip || "No IP assigned"}</div>
            </td>
            <td data-label="${t('th_purchased')}"><span class="num-mono" style="font-weight: 600;">${vps.total_purchased_gb}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">GB</span></td>
            <td data-label="${t('th_current_limit')}"><span class="num-mono">${vps.current_virtualizor_limit_gb}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">GB</span></td>
            <td data-label="${t('th_used')}"><span class="num-mono" style="color: var(--accent-rose);">${vps.current_month_used_gb}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">GB</span></td>
            <td data-label="${t('th_remaining')}"><span class="num-mono" style="color: var(--accent-emerald); font-weight: 700;">${vps.remaining_gb}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">GB</span></td>
            <td data-label="${t('th_progress')}">
                <div style="font-size: 0.8rem;" class="num-mono">${progressPercent}%</div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${progressPercent}%; background: ${progressColor};"></div>
                </div>
            </td>
            <td data-label="${t('th_last_rollover')}"><span class="badge-tag num-mono">${vps.last_rollover_period || "None"}</span></td>
            <td data-label="${t('th_actions')}">
                <button class="glass-btn" style="padding: 6px 12px; font-size: 0.8rem;" onclick="openTopupModal('${vps.vpsid}', '${vps.hostname}')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    <span>${t('btn_add_traffic')}</span>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterVPS() {
    const q = (document.getElementById("vpsSearch").value || "").toLowerCase();
    if (!q) {
        renderVPS(allVpsData);
        return;
    }
    const filtered = allVpsData.filter(v => 
        (v.hostname && v.hostname.toLowerCase().includes(q)) ||
        (v.ip && v.ip.toLowerCase().includes(q)) ||
        (v.vpsid && v.vpsid.toString().includes(q))
    );
    renderVPS(filtered);
}

// --- Sync Node Action ---
async function syncNode() {
    showToast("Connecting to Virtualizor node...", "info");
    try {
        const res = await fetch("/api/system/sync", { method: "POST" });
        const data = await res.json();
        if (data.status === "success") {
            showToast(`${t("toast_sync_success")} (${data.total_vps} VPS synced)`, "success");
            loadDashboard();
        } else {
            showToast(data.message || t("toast_sync_failed"), "error");
        }
    } catch (e) {
        showToast(t("toast_sync_failed"), "error");
    }
}

// --- Top-Up Modal ---
function openTopupModal(vpsid, hostname) {
    document.getElementById("modalVpsId").value = vpsid;
    document.getElementById("modalTargetHostname").textContent = `${hostname} (#${vpsid})`;
    document.getElementById("modalAddAmount").value = "";
    document.getElementById("topupModal").classList.add("active");
}

function closeTopupModal() {
    document.getElementById("topupModal").classList.remove("active");
}

async function submitTopup(e) {
    e.preventDefault();
    const vpsid = document.getElementById("modalVpsId").value;
    const gb = parseFloat(document.getElementById("modalAddAmount").value);
    if (!gb || gb <= 0) return;

    try {
        const res = await fetch(`/api/vps/${vpsid}/add-traffic`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ extra_gb: gb })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            closeTopupModal();
            showToast(`${t("toast_add_success")} (+${gb} GB)`, "success");
            loadDashboard();
        } else {
            showToast(data.detail || t("toast_add_failed"), "error");
        }
    } catch (err) {
        showToast(t("toast_add_failed"), "error");
    }
}

// --- Tab Switching & Audit Logs ---
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll(".nav-link").forEach(link => link.classList.remove("active"));
    
    const dashTab = document.getElementById("tabDashboard");
    const logsTab = document.getElementById("tabLogs");
    const pageHeading = document.getElementById("pageHeading");

    if (tab === "dashboard") {
        dashTab.style.display = "block";
        logsTab.style.display = "none";
        pageHeading.textContent = t("nav_dashboard");
        loadDashboard();
    } else if (tab === "logs") {
        dashTab.style.display = "none";
        logsTab.style.display = "block";
        pageHeading.textContent = t("nav_logs");
        loadLogs();
    }
}

async function loadLogs() {
    try {
        const res = await fetch("/api/logs?limit=80");
        if (res.ok) {
            const data = await res.json();
            renderLogs(data.logs || []);
        }
    } catch (e) {
        console.error("Error loading logs", e);
    }
}

function renderLogs(logs) {
    const tbody = document.getElementById("logsTableBody");
    tbody.innerHTML = "";

    if (!logs || logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 30px;">No audit logs recorded yet.</td></tr>`;
        return;
    }

    logs.forEach(l => {
        const tr = document.createElement("tr");
        let badgeColor = "var(--border-subtle)";
        if (l.event_type === "ROLLOVER") badgeColor = "var(--accent-indigo)";
        else if (l.event_type === "ADD_TRAFFIC") badgeColor = "var(--accent-emerald)";

        tr.innerHTML = `
            <td data-label="${t('th_log_time')}"><span class="num-mono" style="font-size: 0.82rem;">${l.timestamp}</span></td>
            <td data-label="${t('th_log_event')}"><span class="badge-tag" style="border-color: ${badgeColor};">${l.event_type}</span></td>
            <td data-label="${t('th_log_vps')}"><span class="badge-tag num-mono">#${l.vpsid}</span></td>
            <td data-label="${t('th_log_message')}">${l.message}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    setLanguage(currentLang);
    checkAuth();
});
