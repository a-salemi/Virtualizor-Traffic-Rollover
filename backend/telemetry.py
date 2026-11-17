import os
import shutil
import time
import platform
import logging

logger = logging.getLogger("virturoll.telemetry")

# Prime psutil baseline on module import
try:
    import psutil
    psutil.cpu_percent(interval=None)
except Exception:
    psutil = None

def get_uptime_str(seconds: float) -> str:
    if seconds <= 0:
        return "0m"
    days = int(seconds // (24 * 3600))
    hours = int((seconds % (24 * 3600)) // 3600)
    minutes = int((seconds % 3600) // 60)
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def get_system_telemetry() -> dict:
    cores = os.cpu_count() or 1
    cpu_percent = 0.0
    load_avg = [0.0, 0.0, 0.0]

    # Load average
    try:
        if hasattr(os, "getloadavg"):
            l1, l5, l15 = os.getloadavg()
            load_avg = [round(l1, 2), round(l5, 2), round(l15, 2)]
            cpu_percent = min(100.0, round((l1 / cores) * 100, 1))
    except Exception:
        pass

    mem_total_gb = 1.0
    mem_used_gb = 0.0
    mem_percent = 0.0
    swap_total_gb = 0.0
    swap_used_gb = 0.0
    swap_percent = 0.0
    uptime_seconds = 0.0

    # Try psutil first
    if psutil:
        try:
            # CPU
            instant_cpu = psutil.cpu_percent(interval=None)
            if instant_cpu > 0:
                cpu_percent = round(instant_cpu, 1)

            # RAM
            vm = psutil.virtual_memory()
            mem_total_gb = round(vm.total / (1024**3), 2)
            mem_used_gb = round((vm.total - vm.available) / (1024**3), 2)
            mem_percent = round(vm.percent, 1)

            # Swap
            sw = psutil.swap_memory()
            swap_total_gb = round(sw.total / (1024**3), 2)
            swap_used_gb = round(sw.used / (1024**3), 2)
            swap_percent = round(sw.percent, 1) if sw.total > 0 else 0.0

            # Uptime
            uptime_seconds = time.time() - psutil.boot_time()
        except Exception as e:
            logger.debug(f"psutil telemetry error: {e}")

    # Fallback /proc for Linux
    if mem_used_gb == 0.0 and os.path.exists("/proc/meminfo"):
        try:
            mem_data = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        k = parts[0].strip()
                        v = parts[1].strip().split()[0]
                        try:
                            mem_data[k] = int(v) * 1024
                        except ValueError:
                            pass
            total = mem_data.get("MemTotal", 1024**3)
            avail = mem_data.get("MemAvailable", mem_data.get("MemFree", 0))
            used = total - avail
            mem_total_gb = round(total / (1024**3), 2)
            mem_used_gb = round(used / (1024**3), 2)
            mem_percent = round((used / total) * 100, 1) if total > 0 else 0.0

            sw_total = mem_data.get("SwapTotal", 0)
            sw_free = mem_data.get("SwapFree", 0)
            sw_used = sw_total - sw_free
            swap_total_gb = round(sw_total / (1024**3), 2)
            swap_used_gb = round(sw_used / (1024**3), 2)
            swap_percent = round((sw_used / sw_total) * 100, 1) if sw_total > 0 else 0.0
        except Exception:
            pass

    if uptime_seconds <= 0 and os.path.exists("/proc/uptime"):
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
        except Exception:
            pass

    # Disk Usage
    disk_total_gb = 10.0
    disk_used_gb = 1.0
    disk_percent = 10.0
    try:
        total, used, free = shutil.disk_usage("/")
        disk_total_gb = round(total / (1024**3), 2)
        disk_used_gb = round(used / (1024**3), 2)
        disk_percent = round((used / total) * 100, 1) if total > 0 else 0.0
    except Exception:
        pass

    uptime_str = get_uptime_str(uptime_seconds)

    # Provide both nested and flat keys for complete client-side compatibility
    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "uptime": uptime_str,
        "uptime_formatted": uptime_str,
        "uptime_seconds": int(uptime_seconds),
        "cpu_usage_pct": cpu_percent,
        "cpu_count": cores,
        "load_average": load_avg,
        "cpu": {
            "percent": cpu_percent,
            "pct": cpu_percent,
            "cores": cores,
            "load_avg": load_avg
        },
        "memory": {
            "percent": mem_percent,
            "pct": mem_percent,
            "used_gb": mem_used_gb,
            "total_gb": mem_total_gb
        },
        "ram": {
            "percent": mem_percent,
            "pct": mem_percent,
            "used_gb": mem_used_gb,
            "total_gb": mem_total_gb
        },
        "swap": {
            "percent": swap_percent,
            "pct": swap_percent,
            "used_gb": swap_used_gb,
            "total_gb": swap_total_gb
        },
        "disk": {
            "percent": disk_percent,
            "pct": disk_percent,
            "used_gb": disk_used_gb,
            "total_gb": disk_total_gb
        }
    }
