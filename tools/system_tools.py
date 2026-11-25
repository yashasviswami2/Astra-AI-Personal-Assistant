import psutil
import platform
from datetime import datetime, timedelta
from pathlib import Path


def get_system_status() -> str:
    """Retrieve live CPU, RAM, disk and battery information."""

    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.home().anchor)
    battery = psutil.sensors_battery()

    battery_status = "Not available"

    if battery:
        battery_status = (
            f"{battery.percent}% - "
            f"{'Charging' if battery.power_plugged else 'On battery'}"
        )

    return (
        f"CPU Usage: {cpu}%\n"
        f"RAM Usage: {ram.percent}%\n"
        f"Total RAM: {ram.total / (1024 ** 3):.2f} GB\n"
        f"Available RAM: {ram.available / (1024 ** 3):.2f} GB\n"
        f"Disk Usage: {disk.percent}%\n"
        f"Free Storage: {disk.free / (1024 ** 3):.2f} GB\n"
        f"Battery: {battery_status}"
    )


def get_system_information() -> str:
    """Retrieve operating system and hardware information."""

    return (
        f"Operating System: {platform.system()}\n"
        f"OS Version: {platform.release()}\n"
        f"Architecture: {platform.machine()}\n"
        f"Physical CPU Cores: {psutil.cpu_count(logical=False)}\n"
        f"Logical CPU Cores: {psutil.cpu_count(logical=True)}\n"
        f"Processor: {platform.processor()}"
    )


def get_battery_status() -> str:
    """Retrieve battery percentage and charging status."""

    battery = psutil.sensors_battery()

    if battery is None:
        return "Battery information is not available."

    return (
        f"Battery: {battery.percent}%\n"
        f"Charging: {'Yes' if battery.power_plugged else 'No'}"
    )


def get_system_uptime() -> str:
    """Calculate how long the computer has been running."""

    boot_time = datetime.fromtimestamp(psutil.boot_time())

    uptime = datetime.now() - boot_time

    return (
        f"Last Boot: {boot_time:%Y-%m-%d %H:%M:%S}\n"
        f"System Uptime: {timedelta(seconds=int(uptime.total_seconds()))}"
    )


def analyze_system_performance() -> str:
    """Analyze current resource usage and suggest improvements."""

    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage(Path.home().anchor).percent

    suggestions = []

    if cpu > 80:
        suggestions.append(
            "CPU usage is high. Close unnecessary applications."
        )

    if ram > 80:
        suggestions.append(
            "Memory usage is high. Close unused browser tabs."
        )

    if disk > 90:
        suggestions.append(
            "Storage is nearly full. Review unnecessary files."
        )

    if not suggestions:
        suggestions.append(
            "Current resource usage is within normal limits."
        )

    return (
        f"CPU: {cpu}%\n"
        f"RAM: {ram}%\n"
        f"Disk: {disk}%\n\n"
        + "\n".join(suggestions)
    )