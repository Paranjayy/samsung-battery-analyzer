#!/usr/bin/env python3
"""
Samsung Battery Analyzer v2
===========================
Parses Samsung dumpstate/dumpState log files and extracts battery health data.
Works with SysDump logs from *#9900# menu on Samsung devices.

Supports:
  - Samsung Galaxy A31, S24, S25, and other Samsung devices
  - Both old format (dumpstate.txt) and new format (dumpState_*.log)
  - EFS buffer parsing for detailed battery history
  - App-level battery usage breakdown
  - Multi-device comparison reports
  - First-use date estimation

Usage:
  python3 battery_analyzer.py <file1> [file2] [--json] [--compare] [--apps]
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
    build_date: str = ""
    kernel: str = ""
    network: str = ""
    soc: str = ""
    screen_manufacture_date: str = ""


@dataclass
class BatteryHealth:
    asoc: Optional[int] = None
    usage_cycles_raw: Optional[int] = None
    max_temp: Optional[float] = None
    max_current: Optional[int] = None
    bsoh: Optional[int] = None
    design_capacity_mah: Optional[int] = None
    full_charge_capacity_mah: Optional[int] = None
    capacity_max: Optional[int] = None
    kernel_cycles: Optional[int] = None
    # EFS buffer parsed values
    efs_asoc: Optional[int] = None
    efs_cycles: Optional[int] = None
    efs_design_cap: Optional[int] = None
    efs_full_charge_cap: Optional[int] = None
    efs_max_temp: Optional[float] = None


@dataclass
class BatterySnapshot:
    voltage_mv: Optional[int] = None
    current_ma: Optional[int] = None
    soc_percent: Optional[int] = None
    temp_tenths: Optional[int] = None
    status: str = ""
    health: str = ""


@dataclass
class AppUsage:
    package: str = ""
    uid: str = ""
    active_time: str = ""
    background_time: str = ""
    usage_mah: float = 0.0
    usage_percent: float = 0.0


@dataclass
class ChargeSession:
    last_charge_time: str = ""
    total_discharge_percent: float = 0.0
    total_usage_mah: float = 0.0
    screen_on_time: str = ""
    screen_off_time: str = ""
    apps: list = field(default_factory=list)


@dataclass
class BatteryStats:
    device: DeviceInfo = field(default_factory=DeviceInfo)
    health: BatteryHealth = field(default_factory=BatteryHealth)
    snapshots: list = field(default_factory=list)
    charge_session: ChargeSession = field(default_factory=ChargeSession)
    battery_saver_on: Optional[bool] = None
    battery_level: Optional[int] = None
    screen_on_total: str = ""
    file_size_mb: float = 0.0
    file_name: str = ""


def parse_device_info(line: str, stats: BatteryStats):
    if line.startswith("Build:"):
        stats.device.build = line.split("Build:", 1)[1].strip()
    elif line.startswith("Build fingerprint:"):
        fp = line.split("Build fingerprint:", 1)[1].strip().strip("'")
        parts = fp.split("/")
        if len(parts) >= 2:
            stats.device.model_code = parts[1]
        m = re.search(r":(\d+)/", fp)
        if m:
            stats.device.android_version = m.group(1)
    elif line.startswith("Network:"):
        stats.device.network = line.split("Network:", 1)[1].strip()
    elif "Kernel:" in line and not stats.device.kernel:
        stats.device.kernel = line.split("Kernel:", 1)[1].strip()[:100]


def parse_saved_battery(line: str, stats: BatteryStats):
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


def parse_efs_buf(line: str, stats: BatteryStats):
    """Parse the healthd: efs_buf line for detailed battery history."""
    m = re.search(r"efs_buf:\s*([\d\s-]+)", line)
    if not m:
        return

    values = m.group(1).split()
    if len(values) < 42:
        return

    try:
        vals = [int(v) for v in values]
    except ValueError:
        return

    # EFS buffer layout (Samsung-specific):
    # [36] = ASOC, [7] = cycles, [3-4] = capacity, [16] = max temp
    # [39] = design capacity, [41] = charge state
    if vals[36] > 0 and stats.health.efs_asoc is None:
        stats.health.efs_asoc = vals[36]
    if vals[7] > 0 and stats.health.efs_cycles is None:
        stats.health.efs_cycles = vals[7]
    if vals[3] > 100 and stats.health.efs_design_cap is None:
        stats.health.efs_design_cap = vals[3]
    if vals[4] > 100 and stats.health.efs_full_charge_cap is None:
        stats.health.efs_full_charge_cap = vals[4]
    if vals[16] > 0 and stats.health.efs_max_temp is None:
        stats.health.efs_max_temp = vals[16] / 10.0


def parse_kernel_battery_info(line: str, stats: BatteryStats):
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
    m = re.search(r"Cycle\((\d+)", line)
    if m:
        try:
            stats.health.kernel_cycles = int(m.group(1))
        except ValueError:
            pass

    m = re.search(r"Status\((\w+)\)", line)
    if m and stats.snapshots:
        stats.snapshots[-1].status = m.group(1)

    m = re.search(r"Health\((\w+)\)", line)
    if m and stats.snapshots:
        stats.snapshots[-1].health = m.group(1)


def parse_capacity_info(line: str, stats: BatteryStats):
    m = re.search(r"capacity_max\s*\((\d+)\)", line)
    if m:
        stats.health.capacity_max = int(m.group(1))

    m = re.search(r"CAP_NOM\s+(\d+)mAh", line)
    if m:
        stats.health.design_capacity_mah = int(m.group(1))


def parse_battery_level(line: str, stats: BatteryStats):
    m = re.search(r"mBatteryLevel=(\d+)", line)
    if m:
        stats.battery_level = int(m.group(1))

    if "Battery saver is currently: ON" in line:
        stats.battery_saver_on = True
    elif "Battery saver is currently: OFF" in line:
        stats.battery_saver_on = False

    # Screen on time
    m = re.search(r"Screen on:\s*([\dhms\s]+)", line)
    if m:
        stats.screen_on_total = m.group(1).strip()


def parse_build_date(line: str, stats: BatteryStats):
    m = re.search(r"\[ro\.build\.date\]:\s*\[(.+?)\]", line)
    if m:
        stats.device.build_date = m.group(1)

    m = re.search(r"\[ro\.product\.model\]:\s*\[(.+?)\]", line)
    if m:
        stats.device.model = f"Samsung ({m.group(1)})"

    m = re.search(r"\[ro\.soc\.manufacturer\]:\s*\[(.+?)\]", line)
    if m:
        stats.device.soc = m.group(1)


def parse_charge_session(line: str, stats: BatteryStats):
    """Parse DC.BatteryUsage section for charge session data."""
    if "DC.BatteryUsage" not in line:
        return

    m = re.search(r"Last charge time:\s*(.+)", line)
    if m:
        stats.charge_session.last_charge_time = m.group(1).strip()

    m = re.search(r"TotalDischarge\(%\):\s*([\d.]+)", line)
    if m:
        stats.charge_session.total_discharge_percent = float(m.group(1))

    m = re.search(r"TotalUsage\(mAh\):\s*([\d,]+)", line)
    if m:
        stats.charge_session.total_usage_mah = float(m.group(1).replace(",", ""))

    m = re.search(r"Screen on time:\s*(.+)", line)
    if m:
        stats.charge_session.screen_on_time = m.group(1).strip()

    m = re.search(r"Screen off time:\s*(.+)", line)
    if m:
        stats.charge_session.screen_off_time = m.group(1).strip()

    # Parse app usage lines
    m = re.search(
        r"(\d+)\s*\|\s*(\d+ [hm]\s*(?:\d+ [sm])?)\s*\|\s*([\d hms]+)\s*\|\s*([\d,.]+)\s*\|\s*([\d.]+)\s*\|\s*(\S+)",
        line,
    )
    if m:
        app = AppUsage(
            uid=m.group(1),
            active_time=m.group(2).strip(),
            background_time=m.group(3).strip(),
            usage_mah=float(m.group(4).replace(",", "")),
            usage_percent=float(m.group(5)),
            package=m.group(6),
        )
        stats.charge_session.apps.append(app)


def parse_screen_manufacture(line: str, stats: BatteryStats):
    m = re.search(r"manufactureDate=ManufactureDate\{week=(\d+),\s*year=(\d+)\}", line)
    if m:
        week = int(m.group(1))
        year = int(m.group(2))
        # Approximate date from week number
        try:
            dt = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
            stats.device.screen_manufacture_date = dt.strftime("%B %Y (Week %d)" % week)
        except ValueError:
            stats.device.screen_manufacture_date = f"Week {week}, {year}"


def parse_file(file_path: str) -> BatteryStats:
    stats = BatteryStats()
    stats.file_name = os.path.basename(file_path)
    stats.file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    in_battery_dump = False
    in_dc_usage = False
    line_count = 0

    with open(file_path, "r", errors="replace") as f:
        for line in f:
            line_count += 1
            line_stripped = line.strip()

            # Device info (first ~20 lines)
            if line_count <= 20:
                parse_device_info(line_stripped, stats)

            # Build date and properties
            if line_count > 400000:
                parse_build_date(line_stripped, stats)

            # Track battery dump section
            if "DUMP OF SERVICE battery:" in line_stripped:
                in_battery_dump = True
            elif in_battery_dump and line_stripped.startswith("DUMP OF SERVICE "):
                in_battery_dump = False

            if in_battery_dump:
                parse_saved_battery(line_stripped, stats)

            # DC.BatteryUsage section
            if "DC.BatteryUsage" in line_stripped:
                in_dc_usage = True
                parse_charge_session(line_stripped, stats)
            elif (
                in_dc_usage
                and line_stripped.strip()
                and "DC.BatteryUsage" not in line_stripped
            ):
                if line_stripped.startswith("    ") or line_stripped.startswith("\t"):
                    parse_charge_session(line_stripped, stats)
                else:
                    in_dc_usage = False

            # Kernel-level battery data
            if "sec_bat_get_battery_info:" in line_stripped:
                parse_kernel_battery_info(line_stripped, stats)
            elif "sec_bat_monitor_work:" in line_stripped:
                parse_monitor_work(line_stripped, stats)
            elif "capacity_max" in line_stripped or "CAP_NOM" in line_stripped:
                parse_capacity_info(line_stripped, stats)

            # EFS buffer
            if "healthd: efs_buf:" in line_stripped:
                parse_efs_buf(line_stripped, stats)

            # Screen manufacture date
            if "manufactureDate=" in line_stripped and "DisplayDevice" in line_stripped:
                parse_screen_manufacture(line_stripped, stats)

            # System-level battery info
            parse_battery_level(line_stripped, stats)

    # Derive model name from build
    if stats.device.build:
        build = stats.device.build
        if "S921" in build:
            stats.device.model = "Samsung Galaxy S24"
        elif "S926" in build:
            stats.device.model = "Samsung Galaxy S25"
        elif "S928" in build:
            stats.device.model = "Samsung Galaxy S25 Ultra"
        elif "S923" in build:
            stats.device.model = "Samsung Galaxy S25+"
        elif "A315" in build or "A31" in build:
            stats.device.model = "Samsung Galaxy A31"
        elif "A54" in build:
            stats.device.model = "Samsung Galaxy A54"
        elif "A55" in build:
            stats.device.model = "Samsung Galaxy A55"
        elif "A15" in build:
            stats.device.model = "Samsung Galaxy A15"
        else:
            stats.device.model = f"Samsung ({stats.device.model_code})"

    return stats


def calculate_battery_metrics(stats: BatteryStats) -> dict:
    metrics = {}

    # Cycle count
    if stats.health.usage_cycles_raw is not None:
        metrics["cycle_count"] = stats.health.usage_cycles_raw / 100.0
    elif stats.health.kernel_cycles is not None:
        metrics["cycle_count"] = float(stats.health.kernel_cycles)
    elif stats.health.efs_cycles is not None:
        metrics["cycle_count"] = float(stats.health.efs_cycles)

    # ASOC
    if stats.health.asoc is not None:
        metrics["asoc_percent"] = stats.health.asoc
    elif stats.health.efs_asoc is not None:
        metrics["asoc_percent"] = stats.health.efs_asoc

    # BSOH
    if stats.health.bsoh is not None:
        metrics["bsoh_percent"] = stats.health.bsoh

    # Max temp
    if stats.health.max_temp is not None:
        metrics["max_temp_c"] = stats.health.max_temp
    elif stats.health.efs_max_temp is not None:
        metrics["max_temp_c"] = stats.health.efs_max_temp

    # Max current
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
            metrics["max_discharge_ma"] = min(currents)
            metrics["max_charge_ma"] = max(currents)

        metrics["snapshot_count"] = len(stats.snapshots)

    # Design capacity
    if stats.health.design_capacity_mah:
        metrics["design_capacity_mah"] = stats.health.design_capacity_mah
    elif stats.health.efs_design_cap:
        metrics["design_capacity_mah"] = stats.health.efs_design_cap
    elif "A31" in stats.device.model:
        metrics["design_capacity_mah"] = 5000
    elif "S24" in stats.device.model:
        metrics["design_capacity_mah"] = 4000

    # Effective capacity
    if "asoc_percent" in metrics and "design_capacity_mah" in metrics:
        metrics["effective_capacity_mah"] = round(
            metrics["design_capacity_mah"] * metrics["asoc_percent"] / 100.0
        )

    # Health grade
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

    # Cycle-based predictions
    if "cycle_count" in metrics and "asoc_percent" in metrics:
        cycles = metrics["cycle_count"]
        health = metrics["asoc_percent"]

        expected_health = max(100 - (cycles / 500) * 20, 60)
        metrics["expected_health_at_cycles"] = round(expected_health, 1)
        metrics["health_vs_expected"] = round(health - expected_health, 1)

        # Degradation per cycle
        if cycles > 0:
            degradation_per_cycle = (100 - health) / cycles
            metrics["degradation_per_cycle"] = round(degradation_per_cycle, 4)

            # Cycles to 80%
            if health > 80:
                remaining = health - 80
                cycles_to_80 = remaining / degradation_per_cycle
                metrics["cycles_to_80"] = int(cycles_to_80)

                # Time estimates (assuming 0.92 cycles/day)
                days_used = cycles / 0.92
                metrics["est_days_used"] = int(days_used)
                metrics["est_years_used"] = round(days_used / 365, 1)

                remaining_days = cycles_to_80 / 0.92
                metrics["est_remaining_days"] = int(remaining_days)
                metrics["est_remaining_months"] = int(remaining_days / 30)

    return metrics


def format_report(stats: BatteryStats, metrics: dict) -> str:
    lines = []
    d = stats.device
    h = stats.health

    lines.append("=" * 60)
    lines.append(f"  🔋 BATTERY HEALTH REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Device:        {d.model}")
    lines.append(f"  Model Code:    {d.model_code}")
    lines.append(f"  Android:       {d.android_version}")
    lines.append(f"  Build:         {d.build}")
    if d.build_date:
        lines.append(f"  Build Date:    {d.build_date}")
    lines.append(f"  SoC:           {d.soc}")
    lines.append(f"  Network:       {d.network}")
    if d.screen_manufacture_date:
        lines.append(f"  Screen Made:   {d.screen_manufacture_date}")
    lines.append(f"  Log File:      {stats.file_name} ({stats.file_size_mb:.1f} MB)")
    lines.append("")

    lines.append("-" * 60)
    lines.append("  📊 BATTERY HEALTH")
    lines.append("-" * 60)

    if "health_grade" in metrics:
        lines.append(
            f"  Health Grade:      {metrics['health_emoji']} {metrics['health_grade']}"
        )
    if "asoc_percent" in metrics:
        lines.append(f"  ASOC:              {metrics['asoc_percent']}%")
    if "bsoh_percent" in metrics:
        lines.append(f"  BSOH:              {metrics['bsoh_percent']}%")
    if "cycle_count" in metrics:
        lines.append(f"  Cycle Count:       {metrics['cycle_count']:.0f}")
    if "design_capacity_mah" in metrics:
        lines.append(f"  Design Capacity:   {metrics['design_capacity_mah']} mAh")
    if "effective_capacity_mah" in metrics:
        lines.append(f"  Effective Cap:     {metrics['effective_capacity_mah']} mAh")
    if "max_temp_c" in metrics:
        temp_warn = " ⚠️" if metrics["max_temp_c"] > 60 else ""
        lines.append(f"  Max Temp:          {metrics['max_temp_c']}°C{temp_warn}")
    if "max_current_ma" in metrics:
        lines.append(f"  Max Current:       {metrics['max_current_ma']} mA")

    if stats.battery_level is not None:
        lines.append(f"  Current Level:     {stats.battery_level}%")
    if stats.battery_saver_on is not None:
        lines.append(
            f"  Battery Saver:     {'ON' if stats.battery_saver_on else 'OFF'}"
        )

    # EFS data
    if h.efs_asoc is not None or h.efs_cycles is not None:
        lines.append("")
        lines.append("  📦 EFS Buffer (Raw)")
        if h.efs_asoc is not None:
            lines.append(f"    ASOC:            {h.efs_asoc}%")
        if h.efs_cycles is not None:
            lines.append(f"    Cycles:          {h.efs_cycles}")
        if h.efs_design_cap is not None:
            lines.append(f"    Design Cap:      {h.efs_design_cap} mAh")
        if h.efs_full_charge_cap is not None:
            lines.append(f"    Full Charge Cap: {h.efs_full_charge_cap} mAh")
        if h.efs_max_temp is not None:
            lines.append(f"    Max Temp:        {h.efs_max_temp}°C")

    lines.append("")
    lines.append("-" * 60)
    lines.append("  ⚡ LIVE SNAPSHOT DATA")
    lines.append("-" * 60)

    if "snapshot_count" in metrics:
        lines.append(f"  Snapshots:         {metrics['snapshot_count']}")
    if "avg_voltage_mv" in metrics:
        lines.append(f"  Avg Voltage:       {metrics['avg_voltage_mv']} mV")
        lines.append(
            f"  Voltage Range:     {metrics['min_voltage_mv']} - {metrics['max_voltage_mv']} mV"
        )
    if "avg_current_ma" in metrics:
        lines.append(f"  Avg Current:       {metrics['avg_current_ma']} mA")
    if "max_discharge_ma" in metrics:
        lines.append(f"  Max Discharge:     {metrics['max_discharge_ma']} mA")
    if "max_charge_ma" in metrics:
        lines.append(f"  Max Charge:        {metrics['max_charge_ma']} mA")
    if "avg_temp_c" in metrics:
        lines.append(f"  Avg Temp:          {metrics['avg_temp_c']}°C")
        lines.append(
            f"  Temp Range:        {metrics['min_temp_c']}°C - {metrics['max_snapshot_temp_c']}°C"
        )

    # Charge session
    cs = stats.charge_session
    if cs.last_charge_time:
        lines.append("")
        lines.append("-" * 60)
        lines.append("  🔌 LAST CHARGE SESSION")
        lines.append("-" * 60)
        lines.append(f"  Last Charge:       {cs.last_charge_time}")
        lines.append(f"  Total Discharge:   {cs.total_discharge_percent}%")
        lines.append(f"  Total Usage:       {cs.total_usage_mah:.0f} mAh")
        lines.append(f"  Screen On:         {cs.screen_on_time}")
        lines.append(f"  Screen Off:        {cs.screen_off_time}")

    # App usage
    if cs.apps:
        lines.append("")
        lines.append("-" * 60)
        lines.append("  📱 TOP BATTERY DRAINERS")
        lines.append("-" * 60)
        lines.append(f"  {'Rank':<5} {'App':<45} {'mAh':>8} {'%':>6}")
        lines.append("  " + "-" * 64)
        for i, app in enumerate(cs.apps[:15], 1):
            pkg = app.package.split(".")[-1] if "." in app.package else app.package
            # Friendly names
            name_map = {
                "steam": "Steam",
                "whatsapp": "WhatsApp",
                "duolingo": "Duolingo",
                "chrome": "Chrome",
                "youtube": "YouTube",
                "instagram": "Instagram",
                "telegram": "Telegram",
                "flowerfree": "Smart Launcher",
                "launcher": "Samsung Launcher",
                "vending": "Play Store",
                "googlequicksearchbox": "Google App",
                "gmail": "Gmail",
                "gm": "Gmail",
                "gallery3d": "Gallery",
                "camera": "Camera",
                "dialer": "Dialer",
                "systemui": "System UI",
                "honeyboard": "Samsung Keyboard",
                "goodlock": "Good Lock",
                "chatgpt": "ChatGPT",
                "leagueconnect": "LoL Mobile",
                "mShop": "Amazon",
                "samsungapps": "Samsung Apps",
                "easyMover": "Easy Share",
                "photoretouching": "Photo Editor",
                "smartsuggestions": "Smart Suggestions",
                "oneconnect": "SmartThings",
            }
            friendly = name_map.get(pkg, pkg)
            lines.append(
                f"  {i:<5} {friendly:<45} {app.usage_mah:>7.1f} {app.usage_percent:>5.1f}%"
            )

    lines.append("")
    lines.append("-" * 60)
    lines.append("  🔮 PREDICTIONS & INSIGHTS")
    lines.append("-" * 60)

    if "cycle_count" in metrics and "asoc_percent" in metrics:
        if "cycles_to_80" in metrics:
            lines.append(f"  Cycles to 80%:     ~{metrics['cycles_to_80']} more cycles")
        if "est_days_used" in metrics:
            lines.append(
                f"  Est. Days Used:    ~{metrics['est_days_used']} days ({metrics['est_years_used']} years)"
            )
        if "est_remaining_months" in metrics:
            lines.append(
                f"  Est. Remaining:    ~{metrics['est_remaining_months']} months"
            )
        if "health_vs_expected" in metrics:
            diff = metrics["health_vs_expected"]
            if diff > 0:
                lines.append(f"  vs Expected:       +{diff}% (better than avg)")
            elif diff < 0:
                lines.append(f"  vs Expected:       {diff}% (worse than avg)")
        if "degradation_per_cycle" in metrics:
            lines.append(
                f"  Degradation/Cycle: {metrics['degradation_per_cycle'] * 100:.3f}%"
            )

        lines.append("")
        lines.append("  💡 Insights:")
        health = metrics["asoc_percent"]
        cycles = metrics["cycle_count"]
        max_temp = metrics.get("max_temp_c", 0)

        if health >= 90 and cycles > 1000:
            lines.append("  • 🏆 Warrior battery! 90%+ after 1000+ cycles")
        if max_temp > 70:
            lines.append(
                "  • 🔴 CRITICAL: Max temp exceeded 70°C — battery damage likely"
            )
        elif max_temp > 60:
            lines.append(
                "  • 🟠 WARNING: Max temp exceeded 60°C — avoid charging while gaming"
            )
        elif max_temp > 45:
            lines.append("  • 🟡 NOTICE: Max temp was warm — normal for heavy use")
        if health < 80:
            lines.append("  • 🔴 Battery below 80% — consider replacement")
        elif health < 85:
            lines.append("  • 🟡 Battery aging — monitor closely")
        if cycles > 500:
            lines.append(
                "  • High cycle count — battery chemistry is worn but holding up"
            )
        if health >= 90:
            lines.append("  • Battery is in great shape 👍")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_comparison_report(all_stats: list, all_metrics: list) -> str:
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  📱 DEVICE COMPARISON")
    lines.append("=" * 70)
    lines.append("")

    header = f"  {'Metric':<25}"
    for stats in all_stats:
        header += f" {stats.device.model:>20}"
    lines.append(header)
    lines.append("  " + "-" * (25 + 22 * len(all_stats)))

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
        ("Deg/Cycle", lambda m: f"{m.get('degradation_per_cycle', 0) * 100:.3f}%"),
        ("Est. Remaining", lambda m: f"{m.get('est_remaining_months', 'N/A')} mo"),
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
    apps_mode = False

    for arg in sys.argv[1:]:
        if arg == "--json":
            json_mode = True
        elif arg == "--compare":
            compare_mode = True
        elif arg == "--apps":
            apps_mode = True
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
            entry = {
                "device": asdict(stats.device),
                "health": asdict(stats.health),
                "metrics": metrics,
                "snapshot_count": len(stats.snapshots),
                "file": stats.file_name,
                "file_size_mb": round(stats.file_size_mb, 1),
            }
            if stats.charge_session.apps:
                entry["top_apps"] = [
                    {
                        "package": a.package,
                        "mah": a.usage_mah,
                        "percent": a.usage_percent,
                    }
                    for a in stats.charge_session.apps[:10]
                ]
            output.append(entry)
        print(json.dumps(output, indent=2))

    if compare_mode and len(all_stats) > 1:
        print(format_comparison_report(all_stats, all_metrics))


if __name__ == "__main__":
    main()
