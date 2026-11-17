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
            const hash = window.location.hash.replace("#", "") || "dashboard";
            switchTab(hash);
        } else {
            document.getElementById("authView").style.display = "flex";
        }
    } catch (e) {
        document.getElementById("authView").style.display = "flex";
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById("btnLoginSubmit");
    const origText = btn ? btn.textContent : "Authorize Session";
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Authorizing...";
    }
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
            const hash = window.location.hash.replace("#", "") || "dashboard";
            switchTab(hash);
        } else {
            showToast(data.detail || t("login_err"), "error");
        }
    } catch (err) {
        showToast(t("login_err"), "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = origText;
        }
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
        const statusRes = await fetch("/api/system/status");
        if (statusRes.ok) {
            const stats = await statusRes.json();
            document.getElementById("statTotalVps").textContent = stats.total_vps;
            document.getElementById("statManagedBw").textContent = stats.total_managed_bw_gb;
            document.getElementById("statUsedBw").textContent = stats.total_used_bw_gb;
            document.getElementById("statRemainingBw").textContent = stats.total_remaining_bw_gb;
            const sumActive = document.getElementById("sumActiveVps");
            if (sumActive) sumActive.textContent = stats.total_vps;
            const sumPanels = document.getElementById("sumConnectedPanels");
            if (sumPanels) sumPanels.textContent = stats.total_panels || 1;
        }
        fetchTelemetry();
    } catch (e) {
        console.error("Dashboard load error", e);
    }
}

async function loadVPSList() {
    try {
        const vpsRes = await fetch("/api/vps");
        if (vpsRes.ok) {
            const data = await vpsRes.json();
            allVpsData = data.vps || [];
            renderVPS(allVpsData);
        }
    } catch (e) {
        console.error("VPS list load error", e);
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

        const isUnlimited = vps.is_unlimited || vps.current_virtualizor_limit_gb === "Unlimited" || vps.total_purchased_gb === "Unlimited" || vps.current_virtualizor_limit_gb === 0;

        const purchasedHtml = isUnlimited 
            ? `<span class="badge-tag" style="border-color: var(--accent-cyan); color: var(--accent-cyan); font-weight: 600;">∞ Unlimited</span>`
            : `<span class="num-mono" style="font-weight: 600;">${vps.total_purchased_gb}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">GB</span>`;

        const limitHtml = isUnlimited
            ? `<span class="badge-tag" style="border-color: var(--accent-cyan); color: var(--accent-cyan);">∞ Unlimited</span>`
            : `<span class="num-mono">${vps.current_virtualizor_limit_gb}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">GB</span>`;

        const remainingHtml = isUnlimited
            ? `<span class="badge-tag" style="border-color: var(--accent-emerald); color: var(--accent-emerald); font-weight: 700;">∞ Unlimited</span>`
            : `<span class="num-mono" style="color: var(--accent-emerald); font-weight: 700;">${vps.remaining_gb}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">GB</span>`;

        const progressPercent = Math.min(100, Math.max(0, vps.used_percentage || 0));
        let progressColor = "var(--gradient-brand)";
        if (progressPercent > 85) progressColor = "var(--accent-rose)";
        else if (progressPercent > 65) progressColor = "var(--accent-amber)";

        const progressHtml = isUnlimited
            ? `<div style="font-size: 0.8rem; color: var(--text-muted);">∞ No Quota</div>`
            : `<div style="font-size: 0.8rem;" class="num-mono">${progressPercent}%</div>
               <div class="progress-track">
                   <div class="progress-fill" style="width: ${progressPercent}%; background: ${progressColor};"></div>
               </div>`;

        tr.innerHTML = `
            <td data-label="${t('th_vpsid')}"><span class="badge-tag num-mono">#${vps.vpsid}</span></td>
            <td data-label="${t('th_hostname')}">
                <div style="font-weight: 600;">${vps.hostname}</div>
                <div class="num-mono" style="font-size: 0.78rem; color: var(--text-muted);">${vps.ip || "No IP assigned"}</div>
            </td>
            <td data-label="${t('th_purchased')}">${purchasedHtml}</td>
            <td data-label="${t('th_current_limit')}">${limitHtml}</td>
            <td data-label="${t('th_used')}"><span class="num-mono" style="color: var(--accent-rose);">${vps.current_month_used_gb}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">GB</span></td>
            <td data-label="${t('th_remaining')}">${remainingHtml}</td>
            <td data-label="${t('th_progress')}">${progressHtml}</td>
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
            if (currentTab === "vps") {
                loadVPSList();
            }
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
    const msg = document.getElementById("topupModalMsg");
    if (msg) {
        msg.style.display = "none";
        msg.textContent = "";
    }
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

    const form = e.target;
    const submitBtn = form.querySelector("button[type='submit']");
    const origHtml = submitBtn ? submitBtn.innerHTML : "Save";
    const statusMsg = document.getElementById("topupModalMsg");

    if (statusMsg) {
        statusMsg.style.display = "block";
        statusMsg.style.color = "var(--text-secondary)";
        statusMsg.style.border = "1px solid var(--border-glass)";
        statusMsg.textContent = "⏳ " + (t("applying_changes") || "Applying changes to Virtualizor node...");
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>⏳ ${t('applying_changes') || 'Applying...'}</span>`;
    }

    const controller = new AbortController();
    const timeoutTimer = setTimeout(() => controller.abort(), 35000);

    try {
        const res = await fetch(`/api/vps/${vpsid}/add-traffic`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ extra_gb: gb }),
            signal: controller.signal
        });
        clearTimeout(timeoutTimer);
        const data = await res.json();
        if (res.ok && data.success) {
            if (statusMsg) {
                statusMsg.style.color = "var(--accent-emerald)";
                statusMsg.style.borderColor = "var(--accent-emerald)";
                statusMsg.textContent = "✓ " + (data.message || t("toast_add_success"));
            }
            showToast(data.message || `${t("toast_add_success")} (+${gb} GB)`, "success");
            setTimeout(() => {
                closeTopupModal();
                loadVPSList();
                loadDashboard();
            }, 600);
        } else {
            const errMsg = data.message || data.detail || t("toast_add_failed");
            if (statusMsg) {
                statusMsg.style.color = "var(--accent-rose)";
                statusMsg.style.borderColor = "var(--accent-rose)";
                statusMsg.textContent = "✕ " + errMsg;
            }
            showToast(errMsg, "error", 6000);
        }
    } catch (err) {
        clearTimeout(timeoutTimer);
        const errMsg = err.name === "AbortError" 
            ? "Request timed out. Virtualizor node took too long to respond." 
            : (err.message || t("toast_add_failed"));
        if (statusMsg) {
            statusMsg.style.color = "var(--accent-rose)";
            statusMsg.style.borderColor = "var(--accent-rose)";
            statusMsg.textContent = "✕ " + errMsg;
        }
        showToast(errMsg, "error", 6000);
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origHtml;
        }
    }
}

// --- Tab Switching & Audit Logs ---
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll(".nav-link").forEach(link => link.classList.remove("active"));
    const activeNav = document.getElementById("nav" + tab.charAt(0).toUpperCase() + tab.slice(1));
    if (activeNav) activeNav.classList.add("active");
    
    const dashTab = document.getElementById("tabDashboard");
    const vpsTab = document.getElementById("tabVps");
    const panelsTab = document.getElementById("tabPanels");
    const logsTab = document.getElementById("tabLogs");
    const settingsTab = document.getElementById("tabSettings");
    const pageHeading = document.getElementById("pageHeading");
    const crumbCurrent = document.getElementById("crumbCurrent");

    closeMobileSidebar();

    // Hide all tabs
    if (dashTab) dashTab.style.display = "none";
    if (vpsTab) vpsTab.style.display = "none";
    if (panelsTab) panelsTab.style.display = "none";
    if (logsTab) logsTab.style.display = "none";
    if (settingsTab) settingsTab.style.display = "none";

    if (tab === "dashboard") {
        if (dashTab) dashTab.style.display = "block";
        pageHeading.textContent = t("telemetry_title");
        if (crumbCurrent) crumbCurrent.textContent = t("breadcrumb_overview");
        loadDashboard();
        fetchTelemetry();
    } else if (tab === "vps") {
        if (vpsTab) vpsTab.style.display = "block";
        pageHeading.textContent = t("vps_title");
        if (crumbCurrent) crumbCurrent.textContent = t("breadcrumb_vps");
        loadVPSList();
    } else if (tab === "panels") {
        if (panelsTab) panelsTab.style.display = "block";
        pageHeading.textContent = t("panels_title");
        if (crumbCurrent) crumbCurrent.textContent = t("breadcrumb_panels");
        loadPanels();
    } else if (tab === "logs") {
        if (logsTab) logsTab.style.display = "block";
        pageHeading.textContent = t("logs_title");
        if (crumbCurrent) crumbCurrent.textContent = t("breadcrumb_logs");
        loadLogs();
    } else if (tab === "settings") {
        if (settingsTab) settingsTab.style.display = "block";
        pageHeading.textContent = t("settings_page_title");
        if (crumbCurrent) crumbCurrent.textContent = t("breadcrumb_settings");
        loadSettings();
        loadTelegramSettings();
    }
}

// --- Node Settings Management ---
async function loadSettings() {
    try {
        const res = await fetch("/api/settings/node");
        if (res.ok) {
            const data = await res.json();
            document.getElementById("settingNodeIp").value = data.ip || "";
            document.getElementById("settingNodePort").value = data.port || 4085;
            document.getElementById("settingApiKey").value = data.api_key || "";
            
            const passInput = document.getElementById("settingApiPass");
            const badge = document.getElementById("nodeStatusBadge");

            if (data.is_configured) {
                if (passInput) passInput.placeholder = "•••••••••••••••• (Saved - Leave blank to keep)";
                if (badge) {
                    badge.style.borderColor = "var(--accent-emerald)";
                    badge.style.color = "var(--accent-emerald)";
                    badge.textContent = t("status_online");
                }
            } else {
                if (passInput) passInput.placeholder = "Enter API Password";
                if (badge) {
                    badge.style.borderColor = "var(--accent-rose)";
                    badge.style.color = "var(--accent-rose)";
                    badge.textContent = t("status_offline");
                }
            }
        }
    } catch (e) {
        console.error("Error loading settings", e);
    }
}

function cleanInputHost(raw) {
    if (!raw) return "";
    return raw.trim().replace(/^https?:\/\//i, '').split('/')[0].split(':')[0].trim();
}

async function handleSaveSettings(e) {
    e.preventDefault();
    const btn = document.getElementById("btnSaveConn");
    btn.disabled = true;
    
    let rawIp = document.getElementById("settingNodeIp").value;
    const ip = cleanInputHost(rawIp);
    document.getElementById("settingNodeIp").value = ip;

    const port = parseInt(document.getElementById("settingNodePort").value) || 4085;
    const apiKey = document.getElementById("settingApiKey").value.trim();
    const apiPass = document.getElementById("settingApiPass").value.trim();

    try {
        const res = await fetch("/api/settings/node", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ip, port, api_key: apiKey, api_pass: apiPass })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(t("toast_settings_saved"), "success");
            loadSettings();
            syncNode();
        } else {
            showToast(data.detail || "Error saving settings", "error");
        }
    } catch (err) {
        showToast("Error saving settings", "error");
    } finally {
        btn.disabled = false;
    }
}

async function testNodeSettings() {
    const btn = document.getElementById("btnTestConn");
    btn.disabled = true;
    showToast("Testing connection to Virtualizor...", "info");

    let rawIp = document.getElementById("settingNodeIp").value;
    const ip = cleanInputHost(rawIp);
    document.getElementById("settingNodeIp").value = ip;

    const port = parseInt(document.getElementById("settingNodePort").value) || 4085;
    const apiKey = document.getElementById("settingApiKey").value.trim();
    const apiPass = document.getElementById("settingApiPass").value.trim();

    try {
        const res = await fetch("/api/settings/test-connection", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ip, port, api_key: apiKey, api_pass: apiPass })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`${t("toast_test_success")} (${data.vps_count} VPS found)`, "success");
        } else {
            showToast(`${t("toast_test_failed")}: ${data.error || "Unreachable"}`, "error", 6000);
        }
    } catch (err) {
        showToast(`${t("toast_test_failed")}: ${err.message}`, "error");
    } finally {
        btn.disabled = false;
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

window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "");
    if (hash && ["dashboard", "vps", "panels", "logs", "settings"].includes(hash)) {
        switchTab(hash);
    }
});


// --- Real-time Clock ---
function initClock() {
    const clockElem = document.getElementById("liveClock");
    if (!clockElem) return;

    function update() {
        const now = new Date();
        clockElem.textContent = now.toLocaleTimeString();
    }
    update();
    setInterval(update, 1000);
}

// --- Custom Glassmorphic Language Menu (Image 5) ---
function toggleLangMenu(e) {
    if (e) e.stopPropagation();
    const menu = document.getElementById("langMenu");
    if (menu) menu.classList.toggle("show");
}

function selectLanguage(lang) {
    setLanguage(lang);
    const menu = document.getElementById("langMenu");
    if (menu) menu.classList.remove("show");
}

// Close dropdowns on outside click
document.addEventListener("click", (e) => {
    const langBtn = document.getElementById("langDropdownBtn");
    const langMenu = document.getElementById("langMenu");
    if (langMenu && !langMenu.contains(e.target) && (!langBtn || !langBtn.contains(e.target))) {
        langMenu.classList.remove("show");
    }
});

// --- Mobile Sidebar Drawer ---
function toggleMobileSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const backdrop = document.getElementById("mobileBackdrop");
    if (sidebar) sidebar.classList.toggle("open");
    if (backdrop) backdrop.classList.toggle("open");
}

function closeMobileSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const backdrop = document.getElementById("mobileBackdrop");
    if (sidebar) sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("open");
}

// --- Hardware Telemetry Polling (Image 6) ---
async function fetchTelemetry() {
    try {
        const res = await fetch("/api/system/telemetry");
        if (!res.ok) return;
        const data = await res.json();

        // CPU
        const cpuPct = (data.cpu && data.cpu.percent !== undefined) ? data.cpu.percent : (data.cpu_usage_pct || 0);
        document.getElementById("telemCpuPct").textContent = `${Number(cpuPct).toFixed(1)}%`;
        document.getElementById("telemCpuBar").style.width = `${Math.min(100, Math.max(0, cpuPct))}%`;
        const cores = (data.cpu && data.cpu.cores) || data.cpu_count || 1;
        document.getElementById("telemCpuCores").textContent = `${cores} ${t('telemetry_cores')}`;
        const loadArr = (data.cpu && data.cpu.load_avg) || data.load_average;
        if (loadArr && loadArr.length >= 3) {
            const formattedLoad = loadArr.map(n => Number(n).toFixed(2)).join(" / ");
            document.getElementById("telemCpuLoad").textContent = `${t('telemetry_load')}: ${formattedLoad}`;
        }

        // RAM
        const ram = data.memory || data.ram || {};
        const ramPct = ram.percent !== undefined ? ram.percent : (ram.pct || 0);
        document.getElementById("telemRamPct").textContent = `${Number(ramPct).toFixed(1)}%`;
        document.getElementById("telemRamBar").style.width = `${Math.min(100, Math.max(0, ramPct))}%`;
        document.getElementById("telemRamUsed").textContent = `${ram.used_gb || 0} GB / ${ram.total_gb || 0} GB`;
        document.getElementById("telemRamSubPct").textContent = `${Number(ramPct).toFixed(1)}%`;

        // SWAP
        const swap = data.swap || {};
        const swapPct = swap.percent !== undefined ? swap.percent : (swap.pct || 0);
        document.getElementById("telemSwapPct").textContent = `${Number(swapPct).toFixed(1)}%`;
        document.getElementById("telemSwapBar").style.width = `${Math.min(100, Math.max(0, swapPct))}%`;
        document.getElementById("telemSwapUsed").textContent = `${swap.used_gb || 0} GB / ${swap.total_gb || 0} GB`;
        document.getElementById("telemSwapSubPct").textContent = `${Number(swapPct).toFixed(1)}%`;

        // DISK
        const disk = data.disk || {};
        const diskPct = disk.percent !== undefined ? disk.percent : (disk.pct || 0);
        document.getElementById("telemDiskPct").textContent = `${Number(diskPct).toFixed(1)}%`;
        document.getElementById("telemDiskBar").style.width = `${Math.min(100, Math.max(0, diskPct))}%`;
        document.getElementById("telemDiskUsed").textContent = `${disk.used_gb || 0} GB / ${disk.total_gb || 0} GB`;
        document.getElementById("telemDiskSubPct").textContent = `${Number(diskPct).toFixed(1)}%`;

        // Uptime & Counts
        document.getElementById("telemUptime").textContent = data.uptime || data.uptime_formatted || "0d 0h 0m";
        if (document.getElementById("sumActiveVps") && allVpsData && allVpsData.length > 0) {
            document.getElementById("sumActiveVps").textContent = allVpsData.length;
        }
    } catch (e) {
        console.error("Telemetry poll error", e);
    }
}

// Start polling telemetry every 5 seconds
setInterval(() => {
    if (currentTab === "dashboard" && document.getElementById("tabDashboard").style.display !== "none") {
        fetchTelemetry();
    }
}, 5000);

// --- Telegram Bot Settings (Image 1) ---
async function loadTelegramSettings() {
    try {
        const res = await fetch("/api/settings/telegram");
        if (!res.ok) return;
        const cfg = await res.json();
        const toggle = document.getElementById("tgEnabledToggle");
        if (toggle) toggle.checked = !!cfg.enabled;
        document.getElementById("tgBotToken").value = cfg.token || "";
        document.getElementById("tgChatId").value = cfg.chat_id || "";
        document.getElementById("tgProxy").value = cfg.proxy || "";
        document.getElementById("tgApiServer").value = cfg.api_server || "https://api.telegram.org";
    } catch (e) {
        console.error("Error loading Telegram config", e);
    }
}

async function handleSaveTelegram(e) {
    e.preventDefault();
    const btn = document.getElementById("btnSaveTg");
    btn.disabled = true;

    const payload = {
        enabled: document.getElementById("tgEnabledToggle").checked,
        token: document.getElementById("tgBotToken").value.trim(),
        chat_id: document.getElementById("tgChatId").value.trim(),
        proxy: document.getElementById("tgProxy").value.trim(),
        api_server: document.getElementById("tgApiServer").value.trim() || "https://api.telegram.org",
        lang: currentLang
    };

    try {
        const res = await fetch("/api/settings/telegram", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(t("toast_settings_saved"), "success");
        } else {
            showToast(data.detail || "Error saving Telegram settings", "error");
        }
    } catch (err) {
        showToast("Error saving Telegram settings", "error");
    } finally {
        btn.disabled = false;
    }
}

async function testTelegramAlert() {
    const btn = document.getElementById("btnTestTg");
    btn.disabled = true;
    showToast("Sending test notification to Telegram...", "info");

    const token = document.getElementById("tgBotToken").value.trim();
    const chat_id = document.getElementById("tgChatId").value.trim();
    const proxy = document.getElementById("tgProxy").value.trim();
    const api_server = document.getElementById("tgApiServer").value.trim();

    try {
        const res = await fetch("/api/settings/telegram/test", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, chat_id, proxy, api_server })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast("Test message sent successfully to your Telegram!", "success");
        } else {
            showToast(data.detail || data.message || "Telegram delivery failed.", "error", 6000);
        }
    } catch (err) {
        showToast("Failed to communicate with Telegram: " + err.message, "error");
    } finally {
        btn.disabled = false;
    }
}

// --- Web Dashboard Port (Image 2) ---
async function handleSavePort(e) {
    e.preventDefault();
    const port = parseInt(document.getElementById("settingPortNum").value);
    if (!port || port < 1024 || port > 65535) {
        showToast("Invalid port number", "error");
        return;
    }

    try {
        const res = await fetch("/api/settings/port", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ port })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(data.message || t("toast_port_saved"), "success", 7000);
        } else {
            showToast(data.detail || "Error updating port", "error");
        }
    } catch (err) {
        showToast("Failed to update port", "error");
    }
}

// --- Password Change Modal (Image 2) ---
function openPasswordModal() {
    document.getElementById("pwOld").value = "";
    document.getElementById("pwNew").value = "";
    document.getElementById("pwConfirm").value = "";
    document.getElementById("passwordModal").classList.add("active");
}

function closePasswordModal() {
    document.getElementById("passwordModal").classList.remove("active");
}

async function handleChangePassword(e) {
    e.preventDefault();
    const old_password = document.getElementById("pwOld").value;
    const new_password = document.getElementById("pwNew").value;
    const confirm = document.getElementById("pwConfirm").value;

    if (new_password !== confirm) {
        showToast(t("toast_pw_mismatch"), "error");
        return;
    }

    try {
        const res = await fetch("/api/auth/change-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ old_password, new_password })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(t("toast_pw_saved"), "success");
            closePasswordModal();
        } else {
            showToast(data.detail || "Password change failed", "error");
        }
    } catch (err) {
        showToast("Error updating password", "error");
    }
}

// --- Backup & Restore (Image 3) ---
function downloadBackupJson() {
    window.location.href = "/api/settings/backup";
}

async function sendBackupTelegram() {
    showToast("Generating backup and dispatching to Telegram...", "info");
    try {
        const res = await fetch("/api/settings/backup/send-telegram", { method: "POST" });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(t("toast_backup_sent"), "success");
        } else {
            showToast(data.detail || "Error sending backup to Telegram", "error");
        }
    } catch (e) {
        showToast("Failed to send backup to Telegram", "error");
    }
}

function handleRestoreBackup(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(evt) {
        try {
            const data = JSON.parse(evt.target.result);
            if (data && data.version) {
                showToast("Backup file validated successfully!", "success");
            } else {
                showToast("Invalid VirtuRoll backup file.", "error");
            }
        } catch (err) {
            showToast("Failed to parse backup JSON file.", "error");
        }
    };
    reader.readAsText(file);
}

// --- Initialization hook ---
// Ensure clock starts on load
document.addEventListener("DOMContentLoaded", () => {
    initClock();
    fetchTelemetry();
});


// --- Multi-Panel Management Engine ---
let allPanelsData = [];

async function loadPanels() {
    try {
        const res = await fetch("/api/panels");
        if (!res.ok) return;
        const data = await res.json();
        allPanelsData = data.panels || [];
        renderPanels(allPanelsData);
        const sumPanels = document.getElementById("sumConnectedPanels");
        if (sumPanels) sumPanels.textContent = allPanelsData.length || 1;
    } catch (e) {
        console.error("Error loading panels", e);
    }
}

function renderPanels(panels) {
    const tbody = document.getElementById("panelsTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!panels || panels.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">No panels configured yet. Click "+ Add Panel" to connect a node.</td></tr>`;
        return;
    }

    panels.forEach(p => {
        const tr = document.createElement("tr");
        const isOnline = p.last_status === "online";
        const badgeColor = isOnline ? "var(--accent-emerald)" : "var(--accent-rose)";
        const statusText = isOnline ? t("status_online") : t("status_offline");

        tr.innerHTML = `
            <td data-label="${t('th_panel_name')}">
                <div style="font-weight: 700;">${p.name}</div>
                <div class="num-mono" style="font-size: 0.78rem; color: var(--text-muted);">ID: #${p.id}</div>
            </td>
            <td data-label="${t('th_panel_ip')}">
                <div class="num-mono" style="font-weight: 600;">${p.ip}</div>
                <div class="num-mono" style="font-size: 0.78rem; color: var(--text-muted);">Port: ${p.port}</div>
            </td>
            <td data-label="${t('th_panel_status')}">
                <span class="badge-tag" style="border-color: ${badgeColor}; color: ${badgeColor};">● ${statusText}</span>
            </td>
            <td data-label="${t('th_panel_vps')}">
                <span class="badge-tag num-mono" style="font-weight: 700;">${p.vps_count} VPS</span>
            </td>
            <td data-label="${t('th_panel_last_sync')}">
                <span class="num-mono" style="font-size: 0.8rem; color: var(--text-secondary);">${p.last_sync}</span>
            </td>
            <td data-label="${t('th_actions')}">
                <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                    <button class="glass-btn" onclick="testSpecificPanel(${p.id})" style="padding: 5px 10px; font-size: 0.78rem;" title="Test Connection">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    </button>
                    <button class="glass-btn glass-btn-primary" onclick="syncSpecificPanel(${p.id})" style="padding: 5px 10px; font-size: 0.78rem;" title="Sync Panel">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                    </button>
                    <button class="glass-btn" onclick="openPanelModal(${p.id})" style="padding: 5px 10px; font-size: 0.78rem;" title="Edit">
                        <span>✏️</span>
                    </button>
                    <button class="glass-btn" onclick="deleteSpecificPanel(${p.id})" style="padding: 5px 10px; font-size: 0.78rem; color: var(--accent-rose);" title="Delete">
                        <span>🗑️</span>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function openPanelModal(panelId = null) {
    const title = document.getElementById("panelModalTitle");
    const idInput = document.getElementById("panelIdInput");
    const nameInput = document.getElementById("panelNameInput");
    const ipInput = document.getElementById("panelIpInput");
    const portInput = document.getElementById("panelPortInput");
    const keyInput = document.getElementById("panelApiKeyInput");
    const passInput = document.getElementById("panelApiPassInput");

    if (panelId) {
        const p = allPanelsData.find(item => item.id === panelId);
        if (p) {
            if (title) title.textContent = t("modal_panel_edit_title");
            idInput.value = p.id;
            nameInput.value = p.name;
            ipInput.value = p.ip;
            portInput.value = p.port;
            keyInput.value = p.api_key;
            passInput.value = "";
            passInput.placeholder = "•••••••• (Leave blank to keep current)";
        }
    } else {
        if (title) title.textContent = t("modal_panel_title");
        idInput.value = "";
        nameInput.value = "";
        ipInput.value = "";
        portInput.value = 4085;
        keyInput.value = "";
        passInput.value = "";
        passInput.placeholder = "Enter API Password";
    }

    document.getElementById("panelModal").classList.add("active");
}

function closePanelModal() {
    document.getElementById("panelModal").classList.remove("active");
}

async function handleSavePanel(e) {
    e.preventDefault();
    const btn = document.getElementById("btnModalSavePanel");
    btn.disabled = true;

    const id = document.getElementById("panelIdInput").value;
    const name = document.getElementById("panelNameInput").value.trim();
    const ip = cleanInputHost(document.getElementById("panelIpInput").value);
    const port = parseInt(document.getElementById("panelPortInput").value) || 4085;
    const api_key = document.getElementById("panelApiKeyInput").value.trim();
    const api_pass = document.getElementById("panelApiPassInput").value.trim();

    try {
        let res;
        if (id) {
            res = await fetch(`/api/panels/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, ip, port, api_key, api_pass: api_pass || undefined })
            });
        } else {
            res = await fetch("/api/panels", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, ip, port, api_key, api_pass })
            });
        }
        const data = await res.json();
        if (res.ok && data.success) {
            closePanelModal();
            showToast("Panel configuration saved successfully!", "success");
            loadPanels();
        } else {
            showToast(data.detail || "Error saving panel", "error");
        }
    } catch (err) {
        showToast("Error saving panel", "error");
    } finally {
        btn.disabled = false;
    }
}

async function testModalPanel() {
    const btn = document.getElementById("btnModalTestPanel");
    btn.disabled = true;
    showToast("Testing connection...", "info");

    const ip = cleanInputHost(document.getElementById("panelIpInput").value);
    const port = parseInt(document.getElementById("panelPortInput").value) || 4085;
    const api_key = document.getElementById("panelApiKeyInput").value.trim();
    const api_pass = document.getElementById("panelApiPassInput").value.trim();

    try {
        const res = await fetch("/api/settings/test-connection", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ip, port, api_key, api_pass })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`${t("toast_test_success")} (${data.vps_count} VPS found)`, "success");
        } else {
            showToast(`${t("toast_test_failed")}: ${data.error || "Unreachable"}`, "error", 6000);
        }
    } catch (err) {
        showToast(`${t("toast_test_failed")}: ${err.message}`, "error");
    } finally {
        btn.disabled = false;
    }
}

async function testSpecificPanel(panelId) {
    showToast("Testing connection to node...", "info");
    try {
        const res = await fetch(`/api/panels/${panelId}/test`, { method: "POST" });
        const data = await res.json();
        if (data.success) {
            showToast(`${t("toast_test_success")} (${data.vps_count} VPS online)`, "success");
            loadPanels();
        } else {
            showToast(`${t("toast_test_failed")}: ${data.error || "Offline"}`, "error");
        }
    } catch (err) {
        showToast("Test request failed", "error");
    }
}

async function syncSpecificPanel(panelId) {
    showToast("Syncing Virtualizor panel...", "info");
    try {
        const res = await fetch(`/api/panels/${panelId}/sync`, { method: "POST" });
        const data = await res.json();
        if (data.status === "success") {
            showToast(`Panel synced successfully! (${data.total_vps} VPS)`, "success");
            loadPanels();
            loadDashboard();
        } else {
            showToast(data.message || "Sync failed", "error");
        }
    } catch (e) {
        showToast("Sync failed", "error");
    }
}

async function deleteSpecificPanel(panelId) {
    if (!confirm("Are you sure you want to remove this panel connection?")) return;
    try {
        const res = await fetch(`/api/panels/${panelId}`, { method: "DELETE" });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast("Panel removed", "info");
            loadPanels();
        } else {
            showToast("Error deleting panel", "error");
        }
    } catch (e) {
        showToast("Error deleting panel", "error");
    }
}
