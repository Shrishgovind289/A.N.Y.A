import csv
import os
import subprocess
import time

import psutil


def format_uptime(total_seconds: int) -> str:
    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)

    def unit(value: int, name: str) -> str:
        suffix = "" if value == 1 else "s"
        return f"{value} {name}{suffix}"

    parts = []

    if days:
        parts.append(unit(days, "day"))

    if hours:
        parts.append(unit(hours, "hour"))

    if minutes:
        parts.append(unit(minutes, "minute"))

    if not parts:
        parts.append(unit(seconds, "second"))

    return ", ".join(parts)


def bytes_to_gib(value: int) -> float:
    return round(value / (1024 ** 3), 2)


def get_server_status() -> dict:
    uptime_seconds = int(
        time.time() - psutil.boot_time()
    )

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    load_1m, load_5m, load_15m = os.getloadavg()

    return {
        "hostname": os.uname().nodename,
        "uptime_total": {
            "exact": format_uptime(uptime_seconds),
            "note": (
                "This is one continuous total uptime value. "
                "Repeat it exactly without separating the days and hours."
            ),
        },
        "cpu": {
            "measurement_note": (
                "CPU usage is sampled while processing "
                "the ANYA request and may include Ollama inference."
            ),
            "usage_percent_during_request": psutil.cpu_percent(
                interval=0.5
            ),
            "logical_cores": psutil.cpu_count(
                logical=True
            ),
            "physical_cores": psutil.cpu_count(
                logical=False
            ),
            "load_average": {
                "1_minute": round(load_1m, 2),
                "5_minutes": round(load_5m, 2),
                "15_minutes": round(load_15m, 2),
            },
        },
        "memory": {
            "total_gib": bytes_to_gib(memory.total),
            "used_gib": bytes_to_gib(memory.used),
            "available_gib": bytes_to_gib(
                memory.available
            ),
            "usage_percent": memory.percent,
        },
        "root_disk": {
            "total_gib": bytes_to_gib(disk.total),
            "used_gib": bytes_to_gib(disk.used),
            "free_gib": bytes_to_gib(disk.free),
            "usage_percent": disk.percent,
        },
    }

def get_gpu_status() -> dict:
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,temperature.gpu,"
        "utilization.gpu,memory.total,memory.used,memory.free,power.draw",
        "--format=csv,noheader,nounits",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except FileNotFoundError:
        return {
            "available": False,
            "error": "nvidia-smi is not installed.",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "error": "nvidia-smi timed out.",
        }
    except subprocess.CalledProcessError as exc:
        return {
            "available": False,
            "error": exc.stderr.strip() or "nvidia-smi failed.",
        }

    rows = list(csv.reader(result.stdout.strip().splitlines()))

    if not rows:
        return {
            "available": False,
            "error": "No NVIDIA GPU data was returned.",
        }

    gpu_data = []

    for row in rows:
        if len(row) != 8:
            continue

        values = [value.strip() for value in row]

        gpu_data.append(
            {
                "name": values[0],
                "driver_version": values[1],
                "temperature_celsius": int(values[2]),
                "utilization_percent": int(values[3]),
                "memory_total_mib": int(values[4]),
                "memory_used_mib": int(values[5]),
                "memory_free_mib": int(values[6]),
                "power_draw_watts": (
                    None
                    if "N/A" in values[7]
                    else float(values[7])
                ),
            }
        )

    return {
        "available": bool(gpu_data),
        "measurement_note": (
            "GPU utilization is an instantaneous sample taken between "
            "ANYA model-generation stages. A 0 percent reading does not "
            "mean the GPU is generally idle. VRAM usage may indicate that "
            "the Ollama model remains loaded on the GPU."
        ),
        "gpus": gpu_data,
    }



def get_system_health_report() -> dict:
    server = get_server_status()
    gpu = get_gpu_status()

    uptime = server["uptime_total"]["exact"]
    cpu = server["cpu"]
    memory = server["memory"]
    disk = server["root_disk"]

    lines = [
        f"Server uptime: {uptime}.",
        (
            "CPU usage sampled during this request: "
            f"{cpu['usage_percent_during_request']}%. "
            "This may include ANYA and Ollama processing."
        ),
        (
            f"Memory: {memory['used_gib']} GiB used out of "
            f"{memory['total_gib']} GiB total "
            f"({memory['usage_percent']}%)."
        ),
        (
            f"Root disk: {disk['used_gib']} GiB used out of "
            f"{disk['total_gib']} GiB total "
            f"({disk['usage_percent']}%)."
        ),
    ]

    if gpu.get("available") and gpu.get("gpus"):
        gpu_info = gpu["gpus"][0]

        lines.append(
            (
                f"GPU: {gpu_info['name']}, driver "
                f"{gpu_info['driver_version']}, temperature "
                f"{gpu_info['temperature_celsius']} degrees Celsius."
            )
        )

        lines.append(
            (
                "Instantaneous GPU utilization sample: "
                f"{gpu_info['utilization_percent']}%. "
                "This sample alone cannot prove that the GPU is idle."
            )
        )

        lines.append(
            (
                f"GPU memory: {gpu_info['memory_used_mib']} MiB used "
                f"out of {gpu_info['memory_total_mib']} MiB. "
                "Allocated VRAM may indicate that an Ollama model "
                "or another process remains loaded."
            )
        )
    else:
        lines.append(
            "NVIDIA GPU status is unavailable: "
            f"{gpu.get('error', 'unknown error')}."
        )

    return {
        "authoritative_summary": "\n".join(lines),
        "instruction": (
            "Report this summary accurately and concisely. "
            "Do not recalculate values or describe the CPU or GPU "
            "as idle."
        ),
    }
