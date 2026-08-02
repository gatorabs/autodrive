import psutil

PRIORITY_MAP = {
    32: "NORMAL",
    64: "IDLE",
    16384: "BELOW_NORMAL",
    32768: "ABOVE_NORMAL",
    128: "HIGH",
    256: "REALTIME"
}

def get_active_python_processes():
    system_cpu = psutil.cpu_percent(interval=None)
    cores = psutil.cpu_count(logical=True) or 1

    processes = []
    for proc in psutil.process_iter(["name", "pid"]):
        name = proc.info.get("name") or ""
        if "python" not in name.lower():
            continue

        try:
            with proc.oneshot():
                nice = proc.nice()
                memory_mb = proc.memory_info().rss / (1024 * 1024)
                cpu_percent = proc.cpu_percent(interval=None) / cores
                try:
                    io_ct = proc.io_counters()
                    io_mb = (io_ct.read_bytes + io_ct.write_bytes) / (1024 * 1024)
                except (psutil.AccessDenied, AttributeError):
                    io_mb = 0
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        processes.append({
            "name": name,
            "pid": proc.info["pid"],
            "priority": PRIORITY_MAP.get(nice, str(nice)),
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "io_mb": io_mb
        })

    total_ram = sum(p["memory_mb"] for p in processes)

    return {
        "system_cpu": system_cpu,
        "total_ram_mb": total_ram,
        "process_count": len(processes),
        "processes": processes
    }
