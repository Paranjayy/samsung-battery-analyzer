#!/usr/bin/env python3
"""
Samsung Battery Analyzer
========================
Parses Samsung dumpstate/dumpState log files and extracts battery health data.
Works with SysDump logs from *#9900# menu on Samsung devices.

Supports:
  - Samsung Galaxy A31, S24, and other Samsung devices
  - Both old format (dumpstate.txt) and new format (dumpState_*.log)
  - Multi-device comparison reports

Usage:
  python3 battery_analyzer.py <file1> [file2] [--json] [--compare]
"""

import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class DeviceInfo:
    model: str = "Unknown"
    model_code: str = ""
    android_version: str = ""
    build: str = ""
    kernel: str = ""
    network: str = ""


@dataclass
class BatteryHealth:
    asoc: Optional[int] = None  # mSavedBatteryAsoc - Battery ASOC %
    usage_cycles_raw: Optional[int] = None  # mSavedBatteryUsage (raw, divide by 100)
    max_temp: Optional[float] = None  # mSavedBatteryMaxTemp (divide by 10)
    max_current: Optional[int] = None  # mSavedBatteryMaxCurrent (mA)
    bsoh: Optional[int] = None  # mSavedBatteryBsoh (battery state of health)
    design_capacity_mah: Optional[int] = None
    capacity_max: Optional[int] = None  # from fuel gauge
    kernel_cycles: Optional[int] = None  # from sec_bat_monitor_work


@dataclass
class BatterySnapshot:
    voltage_mv: Optional[int] = None
    current_ma: Optional[int] = None
    soc_percent: Optional[int] = None
    temp_tenths: Optional[int] = None
    status: str = ""
    health: str = ""


@dataclass
class BatteryStats:
    device: DeviceInfo = field(default_factory=DeviceInfo)
    health: BatteryHealth = field(default_factory=BatteryHealth)
    snapshots: list = field(default_factory=list)
    battery_saver_on: Optional[bool] = None
    battery_level: Optional[int] = None
    file_size_mb: float = 0.0
    file_name: str = ""


def parse_device_info(line: str, stats: BatteryStats):
    """Extract device info from header lines."""
    if line.startswith("Build:"):
        stats.device.build = line.split("Build:", 1)[1].strip()
    elif line.startswith("Build fingerprint:"):
        fp = line.split("Build fingerprint:", 1)[1].strip().strip("'")
        parts = fp.split("/")
        if len(parts) >= 2:
            stats.device.model_code = parts[1]
        # Extract Android version from fingerprint (e.g., "a31:12" or "e1s:16")
        m = re.search(r":(\d+)/", fp)
        if m:
            stats.device.android_version = m.group(1)
    elif line.startswith("Network:"):
        stats.device.network = line.split("Network:", 1)[1].strip()
    elif "Kernel:" in line and not stats.device.kernel:
        stats.device.kernel = line.split("Kernel:", 1)[1].strip()[:80]


def parse_saved_battery(line: str, stats: BatteryStats):
    """Parse mSavedBattery* lines from DUMP OF SERVICE battery section."""
    m = re.search(r"mSavedBatteryAsoc:\s*\[?(\d+)", line)
    if m:
        stats.health.asoc = int(m.group(1))

    m = re.search(r"mSavedBatteryUsage:\s*\[?(\d+)", line)
    if m:
        stats.health.usage_cycles_raw = int(m.group(1))

    m = re.search(r"mSavedBatteryMaxTemp:\s*(\d+)", line)
    if m:
        stats.health.max_temp = int(m.group(1)) / 10.0

    m = re.search(r"mSavedBatteryMaxCurrent:\s*(\d+)", line)
    if m:
        stats.health.max_current = int(m.group(1))

    m = re.search(r"mSavedBatteryBsoh:\s*(\d+)", line)
    if m:
        stats.health.bsoh = int(m.group(1))


def parse_kernel_battery_info(line: str, stats: BatteryStats):
    """Parse sec_bat_get_battery_info lines for voltage/current/SOC/temp."""
    m = re.search(
        r"sec_bat_get_battery_info:"
        r"Vnow\((\d+)mV\),.*?"
        r"Inow\((-?\d+)mA\),.*?"
        r"SOC\((\d+)%\).*?"
        r"Tbat\((\d+)\)",
        line,
    )
    if m:
        snap = BatterySnapshot(
            voltage_mv=int(m.group(1)),
            current_ma=int(m.group(2)),
            soc_percent=int(m.group(3)),
            temp_tenths=int(m.group(4)),
            status="Charging" if int(m.group(2)) > 0 else "Discharging",
        )
        stats.snapshots.append(snap)


def parse_monitor_work(line: str, stats: BatteryStats):
    """Parse sec_bat_monitor_work for cycle count and status."""
    m = re.search(r"Cycle\((\d+)", line)
    if m:
        try:
            stats.health.kernel_cycles = int(m.group(1))
        except ValueError:
            pass

    m = re.search(r"Status\((\w+)\)", line)
    if m:
        if stats.snapshots:
            stats.snapshots[-1].status = m.group(1)

    m = re.search(r"Health\((\w+)\)", line)
    if m:
        if stats.snapshots:
            stats.snapshots[-1].health = m.group(1)


def parse_capacity_info(line: str, stats: BatteryStats):
    """Parse capacity_max and CAP_NOM from kernel logs."""
    m = re.search(r"capacity_max\s*\((\d+)\)", line)
    if m:
        stats.health.capacity_max = int(m.group(1))

    m = re.search(r"CAP_NOM\s+(\d+)mAh", line)
    if m:
        stats.health.design_capacity_mah = int(m.group(1))


def parse_battery_level(line: str, stats: BatteryStats):
    """Parse battery level from system services."""
    m = re.search(r"mBatteryLevel=(\d+)", line)
    if m:
        stats.battery_level = int(m.group(1))

    if "Battery saver is currently: ON" in line:
        stats.battery_saver_on = True
    elif "Battery saver is currently: OFF" in line:
        stats.battery_saver_on = False


def parse_file(file_path: str) -> BatteryStats:
    """Parse a Samsung dumpstate file and extract battery data."""
    stats = BatteryStats()
    stats.file_name = os.path.basename(file_path)
    stats.file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    in_battery_dump = False
    line_count = 0

    with open(file_path, "r", errors="replace") as f:
        for line in f:
            line_count += 1
            line_stripped = line.strip()

            # Device info (first ~20 lines)
            if line_count <= 20:
                parse_device_info(line_stripped, stats)

            # Track battery dump section
            if "DUMP OF SERVICE battery:" in line_stripped:
                in_battery_dump = True
            elif in_battery_dump and line_stripped.startswith("DUMP OF SERVICE "):
                in_battery_dump = False

            # Parse battery dump section
            if in_battery_dump:
                parse_saved_battery(line_stripped, stats)

            # Kernel-level battery data (fast, these appear thousands of times)
            if "sec_bat_get_battery_info:" in line_stripped:
                parse_kernel_battery_info(line_stripped, stats)
            elif "sec_bat_monitor_work:" in line_stripped:
                parse_monitor_work(line_stripped, stats)
            elif "capacity_max" in line_stripped or "CAP_NOM" in line_stripped:
                parse_capacity_info(line_stripped, stats)

            # System-level battery info
            parse_battery_level(line_stripped, stats)

    # Derive model name from build
    if stats.device.build:
        build = stats.device.build
        if "S921" in build:
            stats.device.model = "Samsung Galaxy S24"
        elif "A315" in build or "A31" in build:
            stats.device.model = "Samsung Galaxy A31"
        elif "S926" in build:
            stats.device.model = "Samsung Galaxy S25"
        elif "S928" in build:
            stats.device.model = "Samsung Galaxy S25 Ultra"
        elif "S923" in build:
            stats.device.model = "Samsung Galaxy S25+"
        else:
            stats.device.model = f"Samsung ({stats.device.model_code})"

    return stats


def calculate_battery_metrics(stats: BatteryStats) -> dict:
    """Calculate derived battery metrics."""
    metrics = {}

    # Cycle count (raw / 100)
    if stats.health.usage_cycles_raw is not None:
        metrics["cycle_count"] = stats.health.usage_cycles_raw / 100.0
    elif stats.health.kernel_cycles is not None:
        metrics["cycle_count"] = float(stats.health.kernel_cycles)

    # ASOC (battery health %)
    if stats.health.asoc is not None:
        metrics["asoc_percent"] = stats.health.asoc

    # BSOH
    if stats.health.bsoh is not None:
        metrics["bsoh_percent"] = stats.health.bsoh

    # Max temp in °C
    if stats.health.max_temp is not None:
        metrics["max_temp_c"] = stats.health.max_temp

    # Max current draw
    if stats.health.max_current is not None:
        metrics["max_current_ma"] = stats.health.max_current

    # Temperature from snapshots
    if stats.snapshots:
        temps = [s.temp_tenths for s in stats.snapshots if s.temp_tenths]
        if temps:
            metrics["avg_temp_c"] = round(sum(temps) / len(temps) / 10.0, 1)
            metrics["min_temp_c"] = min(temps) / 10.0
            metrics["max_snapshot_temp_c"] = max(temps) / 10.0

        voltages = [s.voltage_mv for s in stats.snapshots if s.voltage_mv]
        if voltages:
            metrics["avg_voltage_mv"] = round(sum(voltages) / len(voltages))
            metrics["min_voltage_mv"] = min(voltages)
            metrics["max_voltage_mv"] = max(voltages)

        currents = [s.current_ma for s in stats.snapshots if s.current_ma is not None]
        if currents:
            metrics["avg_current_ma"] = round(sum(currents) / len(currents))
            metrics["max_discharge_ma"] = min(currents)  # most negative
            metrics["max_charge_ma"] = max(currents)

        metrics["snapshot_count"] = len(stats.snapshots)

    # Design capacity
    if stats.health.design_capacity_mah:
        metrics["design_capacity_mah"] = stats.health.design_capacity_mah
    elif "A31" in stats.device.model:
        metrics["design_capacity_mah"] = 5000
    elif "S24" in stats.device.model:
        metrics["design_capacity_mah"] = 4000

    # Effective capacity (ASOC% of design)
    if "asoc_percent" in metrics and "design_capacity_mah" in metrics:
        metrics["effective_capacity_mah"] = round(
            metrics["design_capacity_mah"] * metrics["asoc_percent"] / 100.0
        )

    # Battery degradation score (0=dead, 100=new)
    if "asoc_percent" in metrics:
        health = metrics["asoc_percent"]
        if health >= 95:
            metrics["health_grade"] = "Excellent"
            metrics["health_emoji"] = "🟢"
        elif health >= 85:
            metrics["health_grade"] = "Good"
            metrics["health_emoji"] = "🟡"
        elif health >= 70:
            metrics["health_grade"] = "Fair"
            metrics["health_emoji"] = "🟠"
        else:
            metrics["health_grade"] = "Poor"
            metrics["health_emoji"] = "🔴"

    # Cycle-based degradation estimate
    if "cycle_count" in metrics and "asoc_percent" in metrics:
        cycles = metrics["cycle_count"]
        health = metrics["asoc_percent"]
        # Most batteries retain ~80% after 500 cycles
        expected_health = max(100 - (cycles / 500) * 20, 60)
        metrics["expected_health_at_cycles"] = round(expected_health, 1)
        metrics["health_vs_expected"] = round(health - expected_health, 1)

    return metrics


def format_report(stats: BatteryStats, metrics: dict) -> str:
    """Format a human-readable battery report."""
    lines = []
    d = stats.device
    h = stats.health

    lines.append("=" * 60)
    lines.append(f"  🔋 BATTERY HEALTH REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Device:     {d.model}")
    lines.append(f"  Model Code: {d.model_code}")
    lines.append(f"  Android:    {d.android_version}")
    lines.append(f"  Build:      {d.build}")
    lines.append(f"  Network:    {d.network}")
    lines.append(f"  Log File:   {stats.file_name} ({stats.file_size_mb:.1f} MB)")
    lines.append("")

    lines.append("-" * 60)
    lines.append("  📊 BATTERY HEALTH")
    lines.append("-" * 60)

    if "health_grade" in metrics:
        lines.append(
            f"  Health Grade:   {metrics['health_emoji']} {metrics['health_grade']}"
        )

    if "asoc_percent" in metrics:
        lines.append(f"  ASOC:           {metrics['asoc_percent']}%")
    if "bsoh_percent" in metrics:
        lines.append(f"  BSOH:           {metrics['bsoh_percent']}%")

    if "cycle_count" in metrics:
        lines.append(f"  Cycle Count:    {metrics['cycle_count']:.0f}")

    if "design_capacity_mah" in metrics:
        lines.append(f"  Design Cap:     {metrics['design_capacity_mah']} mAh")
    if "effective_capacity_mah" in metrics:
        lines.append(f"  Effective Cap:  {metrics['effective_capacity_mah']} mAh")

    if "max_temp_c" in metrics:
        lines.append(f"  Max Temp:       {metrics['max_temp_c']}°C")
    if "max_current_ma" in metrics:
        lines.append(f"  Max Current:    {metrics['max_current_ma']} mA")

    if stats.battery_level is not None:
        lines.append(f"  Current Level:  {stats.battery_level}%")
    if stats.battery_saver_on is not None:
        lines.append(f"  Battery Saver:  {'ON' if stats.battery_saver_on else 'OFF'}")

    lines.append("")
    lines.append("-" * 60)
    lines.append("  ⚡ LIVE SNAPSHOT DATA")
    lines.append("-" * 60)

    if "snapshot_count" in metrics:
        lines.append(f"  Snapshots:      {metrics['snapshot_count']}")
    if "avg_voltage_mv" in metrics:
        lines.append(f"  Avg Voltage:    {metrics['avg_voltage_mv']} mV")
        lines.append(
            f"  Voltage Range:  {metrics['min_voltage_mv']} - {metrics['max_voltage_mv']} mV"
        )
    if "avg_current_ma" in metrics:
        lines.append(f"  Avg Current:    {metrics['avg_current_ma']} mA")
    if "max_discharge_ma" in metrics:
        lines.append(f"  Max Discharge:  {metrics['max_discharge_ma']} mA")
    if "max_charge_ma" in metrics:
        lines.append(f"  Max Charge:     {metrics['max_charge_ma']} mA")
    if "avg_temp_c" in metrics:
        lines.append(f"  Avg Temp:       {metrics['avg_temp_c']}°C")
        lines.append(
            f"  Temp Range:     {metrics['min_temp_c']}°C - {metrics['max_snapshot_temp_c']}°C"
        )

    lines.append("")
    lines.append("-" * 60)
    lines.append("  🔮 PREDICTIONS & INSIGHTS")
    lines.append("-" * 60)

    if "cycle_count" in metrics and "asoc_percent" in metrics:
        cycles = metrics["cycle_count"]
        health = metrics["asoc_percent"]

        # Predict remaining life (assuming 80% is end of useful life)
        if health > 80:
            remaining_pct = health - 80
            degradation_per_cycle = (100 - health) / cycles if cycles > 0 else 0
            if degradation_per_cycle > 0:
                cycles_to_80 = remaining_pct / degradation_per_cycle
                lines.append(f"  Est. cycles to 80%:  ~{int(cycles_to_80)} more cycles")

                # Estimate daily cycles based on typical usage
                days_used = cycles / 0.92  # ~0.92 cycles/day from chat
                lines.append(
                    f"  Est. days used:      ~{int(days_used)} days ({int(days_used / 365 * 10) / 10} years)"
                )
                est_remaining_days = cycles_to_80 / 0.92
                lines.append(
                    f"  Est. remaining:      ~{int(est_remaining_days)} days ({int(est_remaining_days / 30)} months)"
                )

        if "health_vs_expected" in metrics:
            diff = metrics["health_vs_expected"]
            if diff > 0:
                lines.append(f"  Health vs Expected:  +{diff}% (better than avg)")
            elif diff < 0:
                lines.append(f"  Health vs Expected:  {diff}% (worse than avg)")
            else:
                lines.append(f"  Health vs Expected:  On par with average")

        lines.append("")
        lines.append("  💡 Tips:")
        if health < 85:
            lines.append("  • Battery is aging. Consider replacement if below 80%")
        if metrics.get("max_temp_c", 0) > 45:
            lines.append("  • High temps detected. Avoid charging while gaming")
        if cycles > 500:
            lines.append("  • High cycle count. Battery chemistry is worn")
        if health >= 90:
            lines.append("  • Battery is in great shape! Keep it up 👍")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_comparison_report(all_stats: list, all_metrics: list) -> str:
    """Format a comparison report for multiple devices."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  📱 DEVICE COMPARISON")
    lines.append("=" * 70)
    lines.append("")

    # Header
    header = f"  {'Metric':<25}"
    for stats in all_stats:
        header += f" {stats.device.model:>20}"
    lines.append(header)
    lines.append("  " + "-" * (25 + 22 * len(all_stats)))

    # Rows
    rows = [
        ("ASOC", lambda m: f"{m.get('asoc_percent', 'N/A')}%"),
        ("BSOH", lambda m: f"{m.get('bsoh_percent', 'N/A')}%"),
        ("Cycles", lambda m: f"{m.get('cycle_count', 'N/A')}"),
        ("Max Temp", lambda m: f"{m.get('max_temp_c', 'N/A')}°C"),
        ("Max Current", lambda m: f"{m.get('max_current_ma', 'N/A')} mA"),
        ("Design Cap", lambda m: f"{m.get('design_capacity_mah', 'N/A')} mAh"),
        ("Effective Cap", lambda m: f"{m.get('effective_capacity_mah', 'N/A')} mAh"),
        (
            "Health Grade",
            lambda m: f"{m.get('health_emoji', '')} {m.get('health_grade', 'N/A')}",
        ),
        (
            "Android",
            lambda m: stats.device.android_version if hasattr(m, "device") else "N/A",
        ),
    ]

    for label, getter in rows:
        row = f"  {label:<25}"
        for metrics in all_metrics:
            row += f" {str(getter(metrics)):>20}"
        lines.append(row)

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    files = []
    json_mode = False
    compare_mode = False

    for arg in sys.argv[1:]:
        if arg == "--json":
            json_mode = True
        elif arg == "--compare":
            compare_mode = True
        elif os.path.exists(arg):
            files.append(arg)
        else:
            print(f"⚠️  File not found: {arg}")

    if not files:
        print("❌ No valid files provided.")
        sys.exit(1)

    all_stats = []
    all_metrics = []

    for file_path in files:
        if not json_mode:
            print(f"🔍 Parsing: {os.path.basename(file_path)}...")
        stats = parse_file(file_path)
        metrics = calculate_battery_metrics(stats)
        all_stats.append(stats)
        all_metrics.append(metrics)

        if not json_mode:
            report = format_report(stats, metrics)
            print(report)

    if json_mode:
        output = []
        for stats, metrics in zip(all_stats, all_metrics):
            output.append(
                {
                    "device": asdict(stats.device),
                    "health": asdict(stats.health),
                    "metrics": metrics,
                    "snapshot_count": len(stats.snapshots),
                    "file": stats.file_name,
                    "file_size_mb": round(stats.file_size_mb, 1),
                }
            )
        print(json.dumps(output, indent=2))

    if compare_mode and len(all_stats) > 1:
        print(format_comparison_report(all_stats, all_metrics))


if __name__ == "__main__":
    main()
