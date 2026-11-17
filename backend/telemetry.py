import os
import shutil
import time
import platform
import logging

logger = logging.getLogger("virturoll.telemetry")

def get_uptime_str(seconds: float) -> str:
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
    # 1. CPU
    cores = os.cpu_count() or 1
    cpu_percent = 0.0
    load_avg = [0.0, 0.0, 0.0]
    
    try:
        if hasattr(os, "getloadavg"):
            load1, load5, load15 = os.getloadavg()
            load_avg = [round(load1, 2), round(load5, 2), round(load15, 2)]
            cpu_percent = min(100.0, round((load1 / cores) * 100, 1))
    except Exception:
        pass

    # 2. RAM & Swap
    mem_total_gb = 1.0
    mem_used_gb = 0.1
    mem_percent = 10.0
    swap_total_gb = 0.0
    swap_used_gb = 0.0
    swap_percent = 0.0
    uptime_seconds = 0

    try:
        import psutil
        vm = psutil.virtual_memory()
        mem_total_gb = round(vm.total / (1024**3), 2)
        mem_used_gb = round(vm.used / (1024**3), 2)
        mem_percent = round(vm.percent, 1)

        sw = psutil.swap_memory()
        swap_total_gb = round(sw.total / (1024**3), 2)
        swap_used_gb = round(sw.used / (1024**3), 2)
        swap_percent = round(sw.percent, 1)

        cpu_percent = round(psutil.cpu_percent(interval=None), 1)
        uptime_seconds = time.time() - psutil.boot_time()
    except ImportError:
        # Fallback reading from /proc/meminfo on Linux
        if os.path.exists("/proc/meminfo"):
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

        if os.path.exists("/proc/uptime"):
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])

    # 3. Disk Storage
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

    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "uptime": get_uptime_str(uptime_seconds),
        "cpu": {
            "percent": cpu_percent,
            "cores": cores,
            "load_avg": load_avg
        },
        "memory": {
            "percent": mem_percent,
            "used_gb": mem_used_gb,
            "total_gb": mem_total_gb
        },
        "swap": {
            "percent": swap_percent,
            "used_gb": swap_used_gb,
            "total_gb": swap_total_gb
        },
        "disk": {
            "percent": disk_percent,
            "used_gb": disk_used_gb,
            "total_gb": disk_total_gb
        }
    }
