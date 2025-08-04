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
    for proc in psutil.process_iter(["name", "pid", "nice", "memory_info", "io_counters"]):
        name = proc.info.get("name") or ""
        if "python" not in name.lower():
            continue

        pid = proc.info["pid"]
        nice = proc.info["nice"]
        priority = PRIORITY_MAP.get(nice, str(nice))
        memory_mb = proc.info["memory_info"].rss / (1024 * 1024)
        cpu_percent = proc.cpu_percent(interval=None) / cores
        io_ct = proc.info.get("io_counters")
        io_mb = ((io_ct.read_bytes + io_ct.write_bytes) / (1024 * 1024)) if io_ct else 0

        processes.append({
            "name": name,
            "pid": pid,
            "priority": priority,
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
