/**
 * VirtuRoll - Internationalization & Translation Dictionary
 * Full Bilingual Support: English (LTR) & Persian (RTL)
 */

const translations = {
    en: {
        app_title: "VirtuRoll",
        app_subtitle: "Persistent VPS Bandwidth Guardian",
        nav_dashboard: "Overview",
        nav_vps_list: "VPS Instances",
        nav_logs: "Activity Logs",
        nav_settings: "Settings",
        nav_node_settings: "Node Connection",
        nav_logout: "Sign Out",
        
        breadcrumb_root: "VirtuRoll",
        breadcrumb_overview: "Overview",
        breadcrumb_logs: "Activity Logs",
        breadcrumb_settings: "Settings",

        // Hardware Telemetry
        telemetry_title: "Overview",
        telemetry_subtitle: "Live hardware telemetry and automated service statuses",
        telemetry_cpu: "CPU USAGE",
        telemetry_ram: "MEMORY (RAM)",
        telemetry_swap: "SWAP USAGE",
        telemetry_disk: "DISK STORAGE",
        telemetry_cores: "Cores",
        telemetry_load: "Load",
        telemetry_uptime: "UPTIME",
        telemetry_connected_nodes: "CONNECTED PANELS",
        telemetry_active_vps: "ACTIVE INSTANCES",

        // Metrics
        stat_total_vps: "Total VPS Nodes",
        stat_managed_bw: "Managed Bandwidth",
        stat_consumed_bw: "Used This Cycle",
        stat_remaining_bw: "Persistent Remaining",
        stat_node_status: "Virtualizor Status",
        
        status_online: "Connected",
        status_offline: "Unconfigured / Offline",
        badge_unlimited: "Unlimited ∞",
        
        vps_title: "Active Virtual Machines",
        vps_search_placeholder: "Filter by Hostname, IP, or VPS ID...",
        btn_sync_now: "Sync Virtualizor",
        btn_add_traffic: "Add Traffic",
        
        th_vpsid: "ID",
        th_hostname: "Hostname & IP",
        th_purchased: "Purchased Plan",
        th_current_limit: "Current Virtualizor Limit",
        th_used: "Used Cycle",
        th_remaining: "Actual Remaining",
        th_progress: "Usage",
        th_last_rollover: "Last Rollover",
        th_actions: "Actions",

        modal_add_title: "Top-Up VPS Traffic",
        modal_add_desc: "Add persistent traffic bucket to VPS",
        modal_label_gb: "Bandwidth to Add (GB)",
        modal_btn_cancel: "Cancel",
        modal_btn_confirm: "Confirm Top-Up",

        logs_title: "System Audit & Rollover History",
        th_log_time: "Timestamp",
        th_log_event: "Event",
        th_log_vps: "Target VPS",
        th_log_message: "Message Details",

        // Settings Page
        settings_page_title: "Settings",
        settings_page_desc: "Telegram bot alerts, multi-user accounts, backup management, and network port configuration",
        
        // Telegram Bot Card
        tg_title: "Telegram Bot Notifications",
        tg_desc: "Receive real-time alerts whenever a traffic rollover occurs, top-up is applied, or if an error happens.",
        tg_alerts_toggle: "Bot Alerts:",
        tg_token_label: "TELEGRAM BOT TOKEN",
        tg_token_desc: "Obtained from @BotFather in Telegram.",
        tg_chat_id_label: "CHAT ID / CHANNEL ID",
        tg_chat_id_desc: "Your numeric Telegram User ID or Group/Channel ID.",
        tg_proxy_label: "SOCKS PROXY",
        tg_proxy_desc: "Enables SOCKS5 proxy to connect to Telegram (e.g. for filtered servers).",
        tg_api_server_label: "TELEGRAM API SERVER",
        tg_api_server_desc: "Changes Telegram API server for connection. Leave empty to use official API.",
        tg_lang_label: "NOTIFICATION LANGUAGE",
        btn_save_tg: "Save Telegram Settings",
        btn_test_tg: "Send Test Notification",

        // User Management Card
        user_mgmt_title: "User Management & Access Control",
        user_mgmt_desc: "Manage accounts and roles: Admin (full control).",
        th_user_username: "USERNAME",
        th_user_role: "ACCESS ROLE",
        th_user_created: "CREATED AT",
        th_user_actions: "ACTIONS",
        btn_change_pw: "Password",
        btn_add_user: "+ Add User",

        // Port Change Card
        port_title: "Web Dashboard Port",
        port_desc: "Customize the manager listening port (default is 8789).",
        port_number_label: "PORT NUMBER",
        port_hint: "After changing, run systemctl restart virturoll on your server.",
        btn_save_port: "Save Port",

        // Backup & Restore Card
        backup_title: "Backup & Restore",
        backup_desc: "Create a full backup of all panels, schedules, and accounts, or restore from a JSON file.",
        backup_download_title: "Download Backup (.json)",
        backup_download_desc: "Export panels, schedules, users & settings to a downloadable JSON file.",
        backup_restore_title: "Restore from File",
        backup_restore_desc: "Upload a previously saved JSON backup to restore entire fleet state.",
        backup_tg_title: "Send Backup to Telegram",
        backup_tg_desc: "Deliver an instant backup file directly to your configured Telegram bot.",

        // Node Connection Card
        settings_title: "Virtualizor Node Connection",
        settings_desc: "Connect to your Virtualizor dedicated node (local or remote server).",
        label_node_ip: "Server IP or Domain",
        label_node_port: "API Port",
        label_api_key: "Virtualizor API Key",
        label_api_pass: "Virtualizor API Password",
        btn_test_conn: "Test Connection",
        btn_save_settings: "Save & Connect",

        // Password Change Modal
        modal_pw_title: "Change Admin Password",
        modal_old_pw: "Current Password",
        modal_new_pw: "New Password",
        modal_confirm_pw: "Confirm New Password",
        btn_save_pw: "Update Password",

        login_title: "VirtuRoll Portal",
        login_subtitle: "Secure Access to Traffic Management",
        login_user_label: "Username",
        login_pass_label: "Password",
        login_btn: "Authorize Session",
        login_err: "Invalid username or password.",

        select_lang_heading: "SELECT LANGUAGE",

        toast_sync_success: "Node synchronized successfully.",
        toast_sync_failed: "Failed to connect to Virtualizor node.",
        toast_add_success: "Successfully added traffic to VPS.",
        toast_add_failed: "Error topping up bandwidth.",
        toast_login_success: "Authenticated successfully. Welcome back!",
        toast_logout: "Session closed.",
        toast_settings_saved: "Settings saved successfully!",
        toast_test_success: "Connection successful!",
        toast_test_failed: "Connection failed",
        toast_port_saved: "Port updated! Restart service to apply.",
        toast_pw_saved: "Password updated successfully!",
        toast_pw_mismatch: "New passwords do not match.",
        toast_backup_sent: "Backup report sent to Telegram!"
    },
    fa: {
        app_title: "ویرتو رول",
        app_subtitle: "سامانه پایش و حفظ ترافیک سرورهای مجازی",
        nav_dashboard: "نمای کلی",
        nav_vps_list: "سرورهای مجازی",
        nav_logs: "گزارشات فعالیت",
        nav_settings: "تنظیمات کلی",
        nav_node_settings: "اتصال به نود",
        nav_logout: "خروج از حساب",

        breadcrumb_root: "ویرتو رول",
        breadcrumb_overview: "نمای کلی",
        breadcrumb_logs: "گزارشات فعالیت",
        breadcrumb_settings: "تنظیمات کلی",

        // Hardware Telemetry
        telemetry_title: "نمای کلی سیستم",
        telemetry_subtitle: "تله‌متری زنده سخت‌افزار سرور و وضعیت پایش خودکار سرویس‌ها",
        telemetry_cpu: "مصرف پردازنده (CPU)",
        telemetry_ram: "حافظه رم (RAM)",
        telemetry_swap: "حافظه سواپ (SWAP)",
        telemetry_disk: "فضای ذخیره‌سازی دیسک",
        telemetry_cores: "هسته",
        telemetry_load: "میانگین بار",
        telemetry_uptime: "مدت زمان روشن بودن",
        telemetry_connected_nodes: "نودهای متصل",
        telemetry_active_vps: "سرورهای مجازی فعال",

        // Metrics
        stat_total_vps: "تعداد کل سرورها",
        stat_managed_bw: "کل ترافیک تحت پوشش",
        stat_consumed_bw: "مصرف دوره جاری",
        stat_remaining_bw: "مانده واقعی کل",
        stat_node_status: "وضعیت اتصال نود",
        
        status_online: "متصل و فعال",
        status_offline: "قطع / نیازمند تنظیم",
        badge_unlimited: "نامحدود ∞",
        
        vps_title: "مدیریت ماشین‌های مجازی",
        vps_search_placeholder: "جستجو بر اساس نام سرور، آی‌پی یا شناسه...",
        btn_sync_now: "همگام‌سازی با نود",
        btn_add_traffic: "شارژ ترافیک",
        
        th_vpsid: "شناسه",
        th_hostname: "نام هاست و آی‌پی",
        th_purchased: "بسته خریداری شده",
        th_current_limit: "سقف فعلی ویرچوالایزور",
        th_used: "مصرف این ماه",
        th_remaining: "مانده ترافیک واقعی",
        th_progress: "درصد مصرف",
        th_last_rollover: "آخرین رول‌اور",
        th_actions: "عملیات",

        modal_add_title: "افزایش ترافیک سرور مجازی",
        modal_add_desc: "افزایش حجم بسته ترافیکی برای سرور",
        modal_label_gb: "میزان حجم اضافه (گیگابایت)",
        modal_btn_cancel: "انصراف",
        modal_btn_confirm: "ثبت و افزایش ترافیک",

        logs_title: "تاریخچه حسابرسی و رول‌اورها",
        th_log_time: "زمان ثبت",
        th_log_event: "نوع رویداد",
        th_log_vps: "سرور هدف",
        th_log_message: "شرح عملیات",

        // Settings Page
        settings_page_title: "تنظیمات کلی",
        settings_page_desc: "ربات اطلاع‌رسانی تلگرام، حساب کاربری، پشتیبان‌گیری و پیکربندی پورت وب",
        
        // Telegram Bot Card
        tg_title: "اطلاع‌رسانی ربات تلگرام",
        tg_desc: "دریافت آنی پیام‌ها هنگام انجام رول‌اور، شارژ ترافیک سرور یا بروز خطا در ارتباط با نود.",
        tg_alerts_toggle: "ارسال هشدارها:",
        tg_token_label: "توکن ربات تلگرام (BOT TOKEN)",
        tg_token_desc: "توکن دریافتی از BotFather@ در تلگرام.",
        tg_chat_id_label: "شناسه چت یا کانال (CHAT ID)",
        tg_chat_id_desc: "شناسه عددی کاربر، گروه یا کانال تلگرام شما.",
        tg_proxy_label: "پروکسی ساکس ۵ (SOCKS5 PROXY)",
        tg_proxy_desc: "پروکسی اختصاصی برای سرورهای فیلترشده (مثال: socks5://user:pass@host:port)",
        tg_api_server_label: "سرور اختصاصی تلگرام (TELEGRAM API SERVER)",
        tg_api_server_desc: "در صورت استفاده از پروکسی معکوس تلگرام وارد کنید. برای رسمی خالی بگذارید.",
        tg_lang_label: "زبان پیام‌های ارسالی",
        btn_save_tg: "ذخیره تنظیمات تلگرام",
        btn_test_tg: "ارسال پیام تست",

        // User Management Card
        user_mgmt_title: "مدیریت کاربران و سطوح دسترسی",
        user_mgmt_desc: "مدیریت حساب کاربری و امنیت سامانه: مدیر کل (دسترسی کامل).",
        th_user_username: "نام کاربری",
        th_user_role: "نقش دسترسی",
        th_user_created: "تاریخ ایجاد",
        th_user_actions: "عملیات",
        btn_change_pw: "تغییر رمز",
        btn_add_user: "+ افزودن کاربر",

        // Port Change Card
        port_title: "پورت وب داشبورد",
        port_desc: "شخصی‌سازی پورت فعال پنل (پیش‌فرض 8789).",
        port_number_label: "شماره پورت",
        port_hint: "پس از تغییر، دستور systemctl restart virturoll را روی سرور اجرا کنید.",
        btn_save_port: "ذخیره پورت",

        // Backup & Restore Card
        backup_title: "پشتیبان‌گیری و بازیابی",
        backup_desc: "تهیه نسخه کامل از تنظیمات، نودها و اطلاعات سرورها یا بازیابی از فایل JSON.",
        backup_download_title: "دانلود نسخه پشتیبان (.json)",
        backup_download_desc: "خروجی کامل از وضعیت ترافیک، کاربران و تنظیمات به فرمت فایل JSON.",
        backup_restore_title: "بازیابی از فایل",
        backup_restore_desc: "آپلود فایل بک‌آپ برای بازگرداندن کلیه اطلاعات سامانه.",
        backup_tg_title: "ارسال بک‌آپ به تلگرام",
        backup_tg_desc: "تحویل فوری فایل گزارش پشتیبان به ربات تلگرام پیکربندی شده.",

        // Node Connection Card
        settings_title: "تنظیمات اتصال به سرور ویرچوالایزور",
        settings_desc: "مشخصات اتصال به سرور اختصاصی ویرچوالایزور (لوکال یا سرور دیگر) را وارد کنید.",
        label_node_ip: "آی‌پی سرور یا دامنه نود",
        label_node_port: "پورت API نود",
        label_api_key: "کلید API Key",
        label_api_pass: "رمز عبور API Pass",
        btn_test_conn: "تست اتصال",
        btn_save_settings: "ذخیره و اتصال",

        // Password Change Modal
        modal_pw_title: "تغییر رمز عبور مدیر",
        modal_old_pw: "رمز عبور فعلی",
        modal_new_pw: "رمز عبور جدید",
        modal_confirm_pw: "تکرار رمز عبور جدید",
        btn_save_pw: "بروزرسانی رمز عبور",

        login_title: "ورود به ویرتو رول",
        login_subtitle: "دسترسی ایمن به سامانه مدیریت ترافیک",
        login_user_label: "نام کاربری",
        login_pass_label: "رمز عبور",
        login_btn: "ورود به پنل",
        login_err: "نام کاربری یا رمز عبور اشتباه است.",

        select_lang_heading: "انتخاب زبان پنل",

        toast_sync_success: "اطلاعات با موفقیت با نود ویرچوالایزور همگام شد.",
        toast_sync_failed: "خطا در برقراری ارتباط با پنل ویرچوالایزور.",
        toast_add_success: "ترافیک سرور با موفقیت افزایش یافت.",
        toast_add_failed: "خطا در اعمال حجم جدید.",
        toast_login_success: "ورود با موفقیت انجام شد. خوش آمدید!",
        toast_logout: "از حساب کاربری خارج شدید.",
        toast_settings_saved: "تنظیمات با موفقیت ذخیره شد!",
        toast_test_success: "ارتباط با سرور ویرچوالایزور با موفقیت تایید شد!",
        toast_test_failed: "خطا در برقراری اتصال با سرور",
        toast_port_saved: "پورت بروزرسانی شد! سرویس را ری‌استارت کنید.",
        toast_pw_saved: "رمز عبور با موفقیت تغییر یافت!",
        toast_pw_mismatch: "رمز جدید و تکرار آن یکسان نیستند.",
        toast_backup_sent: "گزارش پشتیبان به تلگرام ارسال شد!"
    }
};

let currentLang = localStorage.getItem("virturoll_lang") || "en";

function t(key) {
    if (translations[currentLang] && translations[currentLang][key]) {
        return translations[currentLang][key];
    }
    return (translations.en && translations.en[key]) || key;
}

function setLanguage(lang) {
    if (!translations[lang]) lang = "en";
    currentLang = lang;
    localStorage.setItem("virturoll_lang", lang);

    document.documentElement.setAttribute("lang", lang);
    document.documentElement.setAttribute("dir", lang === "fa" ? "rtl" : "ltr");

    updateUiTranslations();
    updateLangSelectorButton();
}

function updateUiTranslations() {
    document.querySelectorAll("[data-i18n]").forEach(elem => {
        const key = elem.getAttribute("data-i18n");
        const val = t(key);
        if (val) elem.textContent = val;
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(elem => {
        const key = elem.getAttribute("data-i18n-placeholder");
        const val = t(key);
        if (val) elem.setAttribute("placeholder", val);
    });
}

function updateLangSelectorButton() {
    const btnText = document.getElementById("selectedLangLabel");
    const flagBadge = document.getElementById("selectedLangFlag");
    if (currentLang === "fa") {
        if (btnText) btnText.textContent = "فارسی (IR)";
        if (flagBadge) flagBadge.textContent = "IR";
    } else {
        if (btnText) btnText.textContent = "English (US)";
        if (flagBadge) flagBadge.textContent = "US";
    }

    // Update active checkmarks inside dropdown
    document.querySelectorAll(".lang-item").forEach(item => {
        const langVal = item.getAttribute("data-lang");
        const check = item.querySelector(".lang-check");
        if (langVal === currentLang) {
            item.classList.add("active");
            if (check) check.style.display = "inline";
        } else {
            item.classList.remove("active");
            if (check) check.style.display = "none";
        }
    });
}

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    setLanguage(currentLang);
});
