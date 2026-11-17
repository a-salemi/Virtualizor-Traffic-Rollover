/**
 * VirtuRoll - Internationalization & Translation Dictionary
 * Seamless English (LTR) & Persian (RTL) localization
 */

const translations = {
    en: {
        app_title: "VirtuRoll",
        app_subtitle: "Persistent VPS Bandwidth Guardian",
        nav_dashboard: "Dashboard",
        nav_vps_list: "VPS Instances",
        nav_logs: "Audit Logs",
        nav_settings: "Node Settings",
        nav_logout: "Sign Out",
        
        stat_total_vps: "Total VPS Nodes",
        stat_managed_bw: "Managed Bandwidth",
        stat_consumed_bw: "Used This Cycle",
        stat_remaining_bw: "Persistent Remaining",
        stat_node_status: "Virtualizor Status",
        
        status_online: "Connected",
        status_offline: "Unconfigured / Offline",
        
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

        settings_title: "Virtualizor Node Connection",
        settings_desc: "Connect to your Virtualizor dedicated node (local or remote server).",
        label_node_ip: "Server IP or Domain",
        label_node_port: "API Port",
        label_api_key: "Virtualizor API Key",
        label_api_pass: "Virtualizor API Password",
        btn_test_conn: "Test Connection",
        btn_save_settings: "Save & Connect",

        login_title: "VirtuRoll Portal",
        login_subtitle: "Secure Access to Traffic Management",
        login_user_label: "Username",
        login_pass_label: "Password",
        login_btn: "Authorize Session",
        login_err: "Invalid username or password.",

        toast_sync_success: "Node synchronized successfully.",
        toast_sync_failed: "Failed to connect to Virtualizor node.",
        toast_add_success: "Successfully added traffic to VPS.",
        toast_add_failed: "Error topping up bandwidth.",
        toast_login_success: "Authenticated successfully. Welcome back!",
        toast_logout: "Session closed.",
        toast_settings_saved: "Virtualizor credentials saved successfully!",
        toast_test_success: "Connection successful!",
        toast_test_failed: "Connection failed"
    },
    fa: {
        app_title: "ویرتو رول",
        app_subtitle: "سامانه پایش و حفظ ترافیک سرورهای مجازی",
        nav_dashboard: "داشبورد",
        nav_vps_list: "سرورهای مجازی",
        nav_logs: "گزارشات و رول‌اورها",
        nav_settings: "تنظیمات نود و API",
        nav_logout: "خروج از حساب",
        
        stat_total_vps: "تعداد کل سرورها",
        stat_managed_bw: "کل ترافیک تحت پوشش",
        stat_consumed_bw: "مصرف دوره جاری",
        stat_remaining_bw: "مانده واقعی کل",
        stat_node_status: "وضعیت اتصال نود",
        
        status_online: "متصل و فعال",
        status_offline: "قطع / نیازمند تنظیم",
        
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

        settings_title: "تنظیمات اتصال به سرور ویرچوالایزور",
        settings_desc: "مشخصات اتصال به سرور اختصاصی ویرچوالایزور (لوکال یا سرور دیگر) را وارد کنید.",
        label_node_ip: "آی‌پی سرور یا دامنه نود",
        label_node_port: "پورت API نود",
        label_api_key: "کلید API Key",
        label_api_pass: "رمز عبور API Pass",
        btn_test_conn: "تست اتصال",
        btn_save_settings: "ذخیره و اتصال",

        login_title: "ورود به ویرتو رول",
        login_subtitle: "دسترسی ایمن به سامانه مدیریت ترافیک",
        login_user_label: "نام کاربری",
        login_pass_label: "رمز عبور",
        login_btn: "ورود به پنل",
        login_err: "نام کاربری یا رمز عبور اشتباه است.",

        toast_sync_success: "اطلاعات با موفقیت با نود ویرچوالایزور همگام شد.",
        toast_sync_failed: "خطا در برقراری ارتباط با پنل ویرچوالایزور.",
        toast_add_success: "ترافیک سرور با موفقیت افزایش یافت.",
        toast_add_failed: "خطا در اعمال حجم جدید.",
        toast_login_success: "ورود با موفقیت انجام شد. خوش آمدید!",
        toast_logout: "از حساب کاربری خارج شدید.",
        toast_settings_saved: "اطلاعات اتصال نود با موفقیت ذخیره شد!",
        toast_test_success: "ارتباط با سرور ویرچوالایزور با موفقیت تایید شد!",
        toast_test_failed: "خطا در برقراری اتصال با سرور"
    }
};

let currentLang = localStorage.getItem("virturoll_lang") || "en";

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("virturoll_lang", lang);
    const html = document.documentElement;
    html.lang = lang;
    html.dir = lang === "fa" ? "rtl" : "ltr";
    
    // Update all data-i18n elements
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (translations[lang] && translations[lang][key]) {
            el.textContent = translations[lang][key];
        }
    });

    // Update placeholders
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (translations[lang] && translations[lang][key]) {
            el.placeholder = translations[lang][key];
        }
    });

    const langSelect = document.getElementById("langSelector");
    if (langSelect) langSelect.value = lang;
}

function t(key) {
    return (translations[currentLang] && translations[currentLang][key]) || key;
}
