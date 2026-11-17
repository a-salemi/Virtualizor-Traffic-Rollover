from __future__ import annotations
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

_last_cpu_stats = None
_smooth_cpu_pct = None

def get_uptime_str(seconds: float) -> str:
    if seconds <= 0:
        return "0d 0h 0m"
    days = int(seconds // (24 * 3600))
    hours = int((seconds % (24 * 3600)) // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{days}d {hours}h {minutes}m"

def calculate_smooth_cpu() -> float:
    global _last_cpu_stats, _smooth_cpu_pct
    measured = None

    # Method 1: Linux /proc/stat differential calculation (Zero blocking, high accuracy)
    if os.path.exists("/proc/stat"):
        try:
            with open("/proc/stat", "r") as f:
                first_line = f.readline()
            if first_line.startswith("cpu "):
                fields = [float(x) for x in first_line.split()[1:8]]
                user, nice, system, idle, iowait, irq, softirq = fields[:7]
                idle_ticks = idle + iowait
                total_ticks = sum(fields)

                if _last_cpu_stats is not None:
                    prev_total, prev_idle = _last_cpu_stats
                    diff_total = total_ticks - prev_total
                    diff_idle = idle_ticks - prev_idle
                    if diff_total > 0:
                        raw_pct = (1.0 - (diff_idle / diff_total)) * 100.0
                        measured = max(0.0, min(100.0, raw_pct))
                _last_cpu_stats = (total_ticks, idle_ticks)
        except Exception:
            pass

    # Method 2: psutil cpu_times delta fallback
    if measured is None and psutil:
        try:
            times = psutil.cpu_times()
            total = sum(times)
            idle = getattr(times, "idle", 0.0)
            if _last_cpu_stats is not None:
                prev_total, prev_idle = _last_cpu_stats
                diff_total = total - prev_total
                diff_idle = idle - prev_idle
                if diff_total > 0:
                    raw_pct = (1.0 - (diff_idle / diff_total)) * 100.0
                    measured = max(0.0, min(100.0, raw_pct))
            _last_cpu_stats = (total, idle)
        except Exception:
            try:
                measured = psutil.cpu_percent(interval=None)
            except Exception:
                pass

    if measured is None:
        measured = 0.0

    # Smooth values using Exponential Moving Average to prevent wild visual jumping
    if _smooth_cpu_pct is None:
        _smooth_cpu_pct = measured
    else:
        _smooth_cpu_pct = (0.65 * measured) + (0.35 * _smooth_cpu_pct)

    return round(_smooth_cpu_pct, 1)

def get_system_telemetry() -> dict:
    cores = os.cpu_count() or 1
    load_avg = [0.0, 0.0, 0.0]

    mem_total_gb = 1.0
    mem_used_gb = 0.0
    mem_percent = 0.0
    swap_total_gb = 0.0
    swap_used_gb = 0.0
    swap_percent = 0.0
    uptime_seconds = 0.0

    # 1. Load Average: Read from /proc/loadavg on Linux or os.getloadavg()
    if os.path.exists("/proc/loadavg"):
        try:
            with open("/proc/loadavg", "r") as f:
                parts = f.read().strip().split()
                if len(parts) >= 3:
                    load_avg = [round(float(parts[0]), 2), round(float(parts[1]), 2), round(float(parts[2]), 2)]
        except Exception:
            pass
    elif hasattr(os, "getloadavg"):
        try:
            l1, l5, l15 = os.getloadavg()
            load_avg = [round(l1, 2), round(l5, 2), round(l15, 2)]
        except Exception:
            pass

    # 2. CPU Usage %: Smooth and accurate without micro-sampling jitters
    cpu_percent = calculate_smooth_cpu()

    # 3. RAM, Swap & Uptime
    if psutil:
        try:
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

    # Fallback /proc for Linux if psutil is unavailable or missing data
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
