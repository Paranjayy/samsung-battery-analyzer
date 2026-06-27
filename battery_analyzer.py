#!/usr/bin/env python3
"""
Universal Android Battery Analyzer
===================================
Parses battery health data from Samsung, Realme/Oppo, Xiaomi, and generic Android bugreports.

Supported Brands & Diagnostic Methods:
┌─────────────────┬──────────────────┬────────────────────────────────────────┐
│ Brand           │ Diagnostic Code  │ Data Source                            │
├─────────────────┼──────────────────┼────────────────────────────────────────┤
│ Samsung         │ *#9900#          │ SysDump → dumpState_*.log              │
│ Realme/Oppo     │ *#800#           │ Logkit → bugreport or oplus_log        │
│ OnePlus         │ *#800#           │ Logkit → bugreport                     │
│ Xiaomi/Redmi    │ *#*#284#*#*      │ Bugreport → bugreport-*.zip            │
│ POCO            │ *#*#284#*#*      │ Bugreport → bugreport-*.zip            │
│ Google Pixel    │ *#*#284#*#*      │ Bugreport → bugreport-*.zip            │
│ Samsung (alt)   │ *#0*#            │ Hardware test menu (limited)           │
│ Any Android     │ adb bugreport    │ Standard Android bugreport             │
└─────────────────┴──────────────────┴────────────────────────────────────────┘

Usage:
  python3 battery_analyzer.py <file1> [file2] [--json] [--compare] [--brand samsung|realme|xiaomi|auto]

Examples:
  python3 battery_analyzer.py dumpstate.txt
  python3 battery_analyzer.py bugreport-samsung-2026.zip
  python3 battery_analyzer.py phone1.txt phone2.log --compare
  python3 battery_analyzer.py oplus_log.txt --brand realme
"""

import json
import os
import re
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ─── Data Models ────────────────────────────────────────────────────────────


@dataclass
class DeviceInfo:
    brand: str = "Unknown"
    model: str = "Unknown"
    model_code: str = ""
    android_version: str = ""
    build: str = ""
    build_date: str = ""
    kernel: str = ""
    network: str = ""
    soc: str = ""
    screen_manufacture_date: str = ""
    first_use_date: str = ""


@dataclass
class BatteryHealth:
    asoc: Optional[int] = None  # Actual State of Charge %
    bsoh: Optional[int] = None  # Battery State of Health %
    cycle_count: Optional[int] = None
    design_capacity_mah: Optional[int] = None
    full_charge_capacity_mah: Optional[int] = None
    max_temp_c: Optional[float] = None
    max_current_ma: Optional[int] = None
    current_voltage_mv: Optional[int] = None
    current_soc: Optional[int] = None
    health_status: str = ""  # Good, Overheat, Dead, etc.
    charge_status: str = ""  # Charging, Discharging, Full, etc.
    technology: str = ""  # Li-ion, Li-poly, etc.


@dataclass
class BatterySnapshot:
    timestamp: str = ""
    voltage_mv: Optional[int] = None
    current_ma: Optional[int] = None
    soc_percent: Optional[int] = None
    temp_c: Optional[float] = None
    status: str = ""


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
    apps: List[AppUsage] = field(default_factory=list)


@dataclass
class BatteryStats:
    device: DeviceInfo = field(default_factory=DeviceInfo)
    health: BatteryHealth = field(default_factory=BatteryHealth)
    snapshots: List[BatterySnapshot] = field(default_factory=list)
    charge_session: ChargeSession = field(default_factory=ChargeSession)
    battery_level: Optional[int] = None
    battery_saver_on: Optional[bool] = None
    screen_on_total: str = ""
    file_size_mb: float = 0.0
    file_name: str = ""
    parser_brand: str = ""


# ─── Brand-Specific Parsers ─────────────────────────────────────────────────


class SamsungParser:
    """Parser for Samsung dumpstate/dumpState log files.

    Data sources:
    - DUMP OF SERVICE battery → mSavedBatteryAsoc, mSavedBatteryUsage, etc.
    - healthd: efs_buf → raw battery history
    - sec_bat_get_battery_info → live voltage/current/temp
    - sec_bat_monitor_work → cycle count
    - DC.BatteryUsage → per-app battery drain
    """

    @staticmethod
    def can_parse(file_path: str, first_lines: str) -> bool:
        indicators = [
            "samsung",
            "A315",
            "S921",
            "S926",
            "S928",
            "S923",
            "A54",
            "A55",
            "A34",
            "A25",
            "A15",
            "dumpState_",
            "sec-battery",
            "mSavedBattery",
            "One UI",
        ]
        return any(ind in first_lines for ind in indicators)

    @staticmethod
    def parse(file_path: str, stats: BatteryStats):
        stats.parser_brand = "Samsung"
        stats.device.brand = "Samsung"
        in_battery_dump = False
        in_dc_usage = False
        line_count = 0

        with open(file_path, "r", errors="replace") as f:
            for line in f:
                line_count += 1
                ls = line.strip()

                if line_count <= 20:
                    SamsungParser._parse_header(ls, stats)
                if line_count > 400000:
                    SamsungParser._parse_properties(ls, stats)

                if "DUMP OF SERVICE battery:" in ls:
                    in_battery_dump = True
                elif in_battery_dump and ls.startswith("DUMP OF SERVICE "):
                    in_battery_dump = False

                if in_battery_dump:
                    SamsungParser._parse_battery_service(ls, stats)

                if "DC.BatteryUsage" in ls:
                    in_dc_usage = True
                    SamsungParser._parse_dc_usage(ls, stats)
                elif in_dc_usage and ls.strip() and "DC.BatteryUsage" not in ls:
                    if ls.startswith("    ") or ls.startswith("\t"):
                        SamsungParser._parse_dc_usage(ls, stats)
                    else:
                        in_dc_usage = False

                if "sec_bat_get_battery_info:" in ls:
                    SamsungParser._parse_kernel_info(ls, stats)
                elif "sec_bat_monitor_work:" in ls:
                    SamsungParser._parse_monitor_work(ls, stats)
                elif "capacity_max" in ls or "CAP_NOM" in ls:
                    SamsungParser._parse_capacity(ls, stats)
                if "healthd: efs_buf:" in ls:
                    SamsungParser._parse_efs_buf(ls, stats)
                if "manufactureDate=" in ls and "DisplayDevice" in ls:
                    SamsungParser._parse_screen_date(ls, stats)

                SamsungParser._parse_battery_level(ls, stats)

    @staticmethod
    def _parse_header(ls, stats):
        if ls.startswith("Build:"):
            stats.device.build = ls.split("Build:", 1)[1].strip()
        elif ls.startswith("Build fingerprint:"):
            fp = ls.split("Build fingerprint:", 1)[1].strip().strip("'")
            parts = fp.split("/")
            if len(parts) >= 2:
                stats.device.model_code = parts[1]
            m = re.search(r":(\d+)/", fp)
            if m:
                stats.device.android_version = m.group(1)
        elif ls.startswith("Network:"):
            stats.device.network = ls.split("Network:", 1)[1].strip()
        elif "Kernel:" in ls and not stats.device.kernel:
            stats.device.kernel = ls.split("Kernel:", 1)[1].strip()[:100]

    @staticmethod
    def _parse_properties(ls, stats):
        m = re.search(r"\[ro\.build\.date\]:\s*\[(.+?)\]", ls)
        if m:
            stats.device.build_date = m.group(1)
        m = re.search(r"\[ro\.product\.model\]:\s*\[(.+?)\]", ls)
        if m:
            stats.device.model = f"Samsung ({m.group(1)})"
        m = re.search(r"\[ro\.soc\.manufacturer\]:\s*\[(.+?)\]", ls)
        if m:
            stats.device.soc = m.group(1)

    @staticmethod
    def _parse_battery_service(ls, stats):
        for pattern, attr in [
            (r"mSavedBatteryAsoc:\s*\[?(\d+)", "asoc"),
            (r"mSavedBatteryUsage:\s*\[?(\d+)", "usage_raw"),
            (r"mSavedBatteryMaxTemp:\s*(\d+)", "max_temp"),
            (r"mSavedBatteryMaxCurrent:\s*(\d+)", "max_current"),
            (r"mSavedBatteryBsoh:\s*(\d+)", "bsoh"),
        ]:
            m = re.search(pattern, ls)
            if m:
                val = int(m.group(1))
                if attr == "asoc":
                    stats.health.asoc = val
                elif attr == "usage_raw":
                    stats.health.cycle_count = val // 100
                elif attr == "max_temp":
                    stats.health.max_temp_c = val / 10.0
                elif attr == "max_current":
                    stats.health.max_current_ma = val
                elif attr == "bsoh":
                    stats.health.bsoh = val

    @staticmethod
    def _parse_efs_buf(ls, stats):
        m = re.search(r"efs_buf:\s*([\d\s-]+)", ls)
        if not m:
            return
        values = m.group(1).split()
        if len(values) < 42:
            return
        try:
            vals = [int(v) for v in values]
        except ValueError:
            return
        if stats.health.cycle_count is None and vals[7] > 0:
            stats.health.cycle_count = vals[7]
        if stats.health.design_capacity_mah is None and vals[3] > 100:
            stats.health.design_capacity_mah = vals[3]
        if stats.health.full_charge_capacity_mah is None and vals[4] > 100:
            stats.health.full_charge_capacity_mah = vals[4]
        if stats.health.max_temp_c is None and vals[16] > 0:
            stats.health.max_temp_c = vals[16] / 10.0

    @staticmethod
    def _parse_kernel_info(ls, stats):
        m = re.search(
            r"Vnow\((\d+)mV\).*?Inow\((-?\d+)mA\).*?SOC\((\d+)%\).*?Tbat\((\d+)\)", ls
        )
        if m:
            stats.snapshots.append(
                BatterySnapshot(
                    voltage_mv=int(m.group(1)),
                    current_ma=int(m.group(2)),
                    soc_percent=int(m.group(3)),
                    temp_c=int(m.group(4)) / 10.0,
                    status="Charging" if int(m.group(2)) > 0 else "Discharging",
                )
            )

    @staticmethod
    def _parse_monitor_work(ls, stats):
        m = re.search(r"Cycle\((\d+)", ls)
        if m and stats.health.cycle_count is None:
            try:
                stats.health.cycle_count = int(m.group(1))
            except ValueError:
                pass

    @staticmethod
    def _parse_capacity(ls, stats):
        m = re.search(r"CAP_NOM\s+(\d+)mAh", ls)
        if m and stats.health.design_capacity_mah in (None, 0):
            val = int(m.group(1))
            if val > 0:
                stats.health.design_capacity_mah = val

    @staticmethod
    def _parse_screen_date(ls, stats):
        m = re.search(
            r"manufactureDate=ManufactureDate\{week=(\d+),\s*year=(\d+)\}", ls
        )
        if m:
            try:
                dt = datetime.strptime(f"{m.group(2)}-W{m.group(1)}-1", "%Y-W%W-%w")
                stats.device.screen_manufacture_date = dt.strftime("%B %Y")
            except ValueError:
                stats.device.screen_manufacture_date = (
                    f"Week {m.group(1)}, {m.group(2)}"
                )

    @staticmethod
    def _parse_dc_usage(ls, stats):
        if "DC.BatteryUsage" not in ls:
            return
        m = re.search(r"Last charge time:\s*(.+)", ls)
        if m:
            stats.charge_session.last_charge_time = m.group(1).strip()
        m = re.search(r"TotalDischarge\(%\):\s*([\d.]+)", ls)
        if m:
            stats.charge_session.total_discharge_percent = float(m.group(1))
        m = re.search(r"TotalUsage\(mAh\):\s*([\d,]+)", ls)
        if m:
            stats.charge_session.total_usage_mah = float(m.group(1).replace(",", ""))
        m = re.search(r"Screen on time:\s*(.+)", ls)
        if m:
            stats.charge_session.screen_on_time = m.group(1).strip()
        m = re.search(r"Screen off time:\s*(.+)", ls)
        if m:
            stats.charge_session.screen_off_time = m.group(1).strip()
        m = re.search(
            r"(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*([\d,.]+)\s*\|\s*([\d.]+)\s*\|\s*(\S+)",
            ls,
        )
        if m:
            stats.charge_session.apps.append(
                AppUsage(
                    uid=m.group(1),
                    active_time=m.group(2).strip(),
                    background_time=m.group(3).strip(),
                    usage_mah=float(m.group(4).replace(",", "")),
                    usage_percent=float(m.group(5)),
                    package=m.group(6),
                )
            )

    @staticmethod
    def _parse_battery_level(ls, stats):
        m = re.search(r"mBatteryLevel=(\d+)", ls)
        if m:
            stats.battery_level = int(m.group(1))
        if "Battery saver is currently: ON" in ls:
            stats.battery_saver_on = True
        elif "Battery saver is currently: OFF" in ls:
            stats.battery_saver_on = False


class RealmeParser:
    """Parser for Realme/Oppo/OnePlus bugreports and logkit files.

    How to get battery data on Realme/Oppo/OnePlus:
    1. Dial *#800# to open Logkit
    2. Tap "Start Record"
    3. Use phone normally for a few minutes
    4. Tap "Stop Record"
    5. Find the zip in /sdcard/LogKit/
    6. Or: use `adb bugreport` for full bugreport

    Data sources in bugreport:
    - DUMP OF SERVICE batterystats → per-app usage
    - dumpsys battery → current battery state
    - Battery Health HAL → health info
    - /sys/class/power_supply/battery/ → kernel-level data
    """

    @staticmethod
    def can_parse(file_path: str, first_lines: str) -> bool:
        indicators = [
            "oppo",
            "realme",
            "oneplus",
            "oplus",
            "OPLUS",
            "OPPO",
            "REALME",
            "OnePlus",
            "coloros",
            "ColorOS",
            "hydrogen",
            "oxygen",
            "CMF",
        ]
        return any(ind in first_lines for ind in indicators)

    @staticmethod
    def parse(file_path: str, stats: BatteryStats):
        stats.parser_brand = "Realme/Oppo/OnePlus"
        stats.device.brand = "Realme/Oppo/OnePlus"

        with open(file_path, "r", errors="replace") as f:
            for line in f:
                ls = line.strip()
                RealmeParser._parse_standard_battery(ls, stats)
                RealmeParser._parse_dumpsys_battery(ls, stats)
                RealmeParser._parse_health_hal(ls, stats)
                RealmeParser._parse_sysfs(ls, stats)

    @staticmethod
    def _parse_standard_battery(ls, stats):
        """Parse standard Android battery fields found in bugreports."""
        m = re.search(r"DUMP OF SERVICE battery:", ls)
        if m:
            # Next few lines will have battery info
            pass

        # healthinfo section (Oppo/Realme specific)
        m = re.search(r"health_info.*?charge_full\s*=\s*(\d+)", ls)
        if m and stats.health.full_charge_capacity_mah is None:
            stats.health.full_charge_capacity_mah = int(m.group(1))

        m = re.search(r"health_info.*?charge_full_design\s*=\s*(\d+)", ls)
        if m and stats.health.design_capacity_mah is None:
            stats.health.design_capacity_mah = int(m.group(1))

        m = re.search(r"health_info.*?cycle_count\s*=\s*(\d+)", ls)
        if m and stats.health.cycle_count is None:
            stats.health.cycle_count = int(m.group(1))

        m = re.search(r"health_info.*?health\s*=\s*(\d+)", ls)
        if m:
            health_val = int(m.group(1))
            # Android BatteryHealth: 2=Good, 3=Overheat, 4=Dead, 5=OverVoltage, 6=UnspecifiedFailure, 7=Cold
            health_map = {
                2: "Good",
                3: "Overheat",
                4: "Dead",
                5: "Over Voltage",
                6: "Failure",
                7: "Cold",
                1: "Unknown",
            }
            stats.health.health_status = health_map.get(
                health_val, f"Code {health_val}"
            )

    @staticmethod
    def _parse_dumpsys_battery(ls, stats):
        """Parse 'dumpsys battery' output."""
        m = re.search(r"level:\s*(\d+)", ls)
        if m:
            stats.battery_level = int(m.group(1))

        m = re.search(r"health:\s*(\d+)", ls)
        if m and not stats.health.health_status:
            health_val = int(m.group(1))
            health_map = {
                2: "Good",
                3: "Overheat",
                4: "Dead",
                5: "Over Voltage",
                6: "Failure",
                7: "Cold",
            }
            stats.health.health_status = health_map.get(
                health_val, f"Code {health_val}"
            )

        m = re.search(r"temperature:\s*(\d+)", ls)
        if m and stats.health.max_temp_c is None:
            stats.health.max_temp_c = int(m.group(1)) / 10.0

        m = re.search(r"voltage:\s*(\d+)", ls)
        if m and stats.health.current_voltage_mv is None:
            stats.health.current_voltage_mv = int(m.group(1))

        m = re.search(r"technology:\s*(.+)", ls)
        if m:
            stats.health.technology = m.group(1).strip()

        m = re.search(r"status:\s*(\d+)", ls)
        if m:
            status_map = {
                1: "Unknown",
                2: "Charging",
                3: "Discharging",
                4: "Not Charging",
                5: "Full",
            }
            stats.health.charge_status = status_map.get(int(m.group(1)), "Unknown")

        m = re.search(r"manufacturer:\s*(.+)", ls)
        if m:
            stats.device.brand = m.group(1).strip()

        m = re.search(r"model:\s*(.+)", ls)
        if m and stats.device.model == "Unknown":
            stats.device.model = m.group(1).strip()

    @staticmethod
    def _parse_health_hal(ls, stats):
        """Parse Battery Health HAL data (Android 10+)."""
        m = re.search(r"charge_counter.*?(\d+)", ls)
        if m and stats.health.current_soc is None:
            stats.health.current_soc = int(m.group(1))

        m = re.search(r"energy_counter.*?(\d+)", ls)
        if m:
            pass  # Energy in nWh, could convert

    @staticmethod
    def _parse_sysfs(ls, stats):
        """Parse /sys/class/power_supply/battery/ data from bugreport."""
        m = re.search(r"POWER_SUPPLY_CYCLE_COUNT=(\d+)", ls)
        if m and stats.health.cycle_count is None:
            stats.health.cycle_count = int(m.group(1))

        m = re.search(r"POWER_SUPPLY_CHARGE_FULL=(\d+)", ls)
        if m and stats.health.full_charge_capacity_mah is None:
            stats.health.full_charge_capacity_mah = (
                int(m.group(1)) // 1000
            )  # uAh to mAh

        m = re.search(r"POWER_SUPPLY_CHARGE_FULL_DESIGN=(\d+)", ls)
        if m and stats.health.design_capacity_mah is None:
            stats.health.design_capacity_mah = int(m.group(1)) // 1000

        m = re.search(r"POWER_SUPPLY_TEMP=(\d+)", ls)
        if m and stats.health.max_temp_c is None:
            stats.health.max_temp_c = int(m.group(1)) / 10.0

        m = re.search(r"POWER_SUPPLY_VOLTAGE_NOW=(\d+)", ls)
        if m and stats.health.current_voltage_mv is None:
            stats.health.current_voltage_mv = int(m.group(1)) // 1000  # uV to mV

        m = re.search(r"POWER_SUPPLY_CURRENT_NOW=(-?\d+)", ls)
        if m and stats.snapshots:
            stats.snapshots[-1].current_ma = int(m.group(1)) // 1000


class XiaomiParser:
    """Parser for Xiaomi/Redmi/POCO bugreports.

    How to get battery data on Xiaomi:
    1. Dial *#*#284#*#* for bug report
    2. Or dial *#*#64663#*#* for CIT hardware test
    3. Or: Settings → About Phone → tap "MIUI version" 7 times →
       Developer Options → take bug report
    4. Or: adb bugreport

    Xiaomi-specific battery data:
    - mi_battery_info service
    - /data/system/batterystats/
    - kernel: /sys/class/power_supply/battery/
    """

    @staticmethod
    def can_parse(file_path: str, first_lines: str) -> bool:
        indicators = [
            "xiaomi",
            "redmi",
            "poco",
            "Xiaomi",
            "Redmi",
            "POCO",
            "MIUI",
            "miui",
            "HyperOS",
            "hyperos",
            "qualcomm",
            "snapdragon",
            "MediaTek",
            "MTK",
        ]
        return any(ind in first_lines for ind in indicators)

    @staticmethod
    def parse(file_path: str, stats: BatteryStats):
        stats.parser_brand = "Xiaomi/Redmi/POCO"
        stats.device.brand = "Xiaomi"

        with open(file_path, "r", errors="replace") as f:
            for line in f:
                ls = line.strip()
                XiaomiParser._parse_mi_battery(ls, stats)
                XiaomiParser._parse_standard_battery(ls, stats)
                XiaomiParser._parse_sysfs(ls, stats)
                XiaomiParser._parse_mi_props(ls, stats)

    @staticmethod
    def _parse_mi_battery(ls, stats):
        """Parse Xiaomi-specific battery service."""
        m = re.search(r"mi_battery_info.*?cycle_count[=:]\s*(\d+)", ls)
        if m and stats.health.cycle_count is None:
            stats.health.cycle_count = int(m.group(1))

        m = re.search(r"mi_battery_info.*?battery_health[=:]\s*(\d+)", ls)
        if m:
            health_val = int(m.group(1))
            health_map = {
                2: "Good",
                3: "Overheat",
                4: "Dead",
                5: "Over Voltage",
                6: "Failure",
                7: "Cold",
            }
            stats.health.health_status = health_map.get(
                health_val, f"Code {health_val}"
            )

        m = re.search(r"mi_battery_info.*?battery_full_capacity[=:]\s*(\d+)", ls)
        if m and stats.health.full_charge_capacity_mah is None:
            stats.health.full_charge_capacity_mah = int(m.group(1))

        m = re.search(r"mi_battery_info.*?battery_design_capacity[=:]\s*(\d+)", ls)
        if m and stats.health.design_capacity_mah is None:
            stats.health.design_capacity_mah = int(m.group(1))

    @staticmethod
    def _parse_standard_battery(ls, stats):
        """Parse standard Android battery fields."""
        m = re.search(r"level:\s*(\d+)", ls)
        if m:
            stats.battery_level = int(m.group(1))

        m = re.search(r"health:\s*(\d+)", ls)
        if m and not stats.health.health_status:
            health_val = int(m.group(1))
            health_map = {
                2: "Good",
                3: "Overheat",
                4: "Dead",
                5: "Over Voltage",
                6: "Failure",
                7: "Cold",
            }
            stats.health.health_status = health_map.get(
                health_val, f"Code {health_val}"
            )

        m = re.search(r"temperature:\s*(\d+)", ls)
        if m and stats.health.max_temp_c is None:
            stats.health.max_temp_c = int(m.group(1)) / 10.0

        m = re.search(r"voltage:\s*(\d+)", ls)
        if m and stats.health.current_voltage_mv is None:
            stats.health.current_voltage_mv = int(m.group(1))

        m = re.search(r"technology:\s*(.+)", ls)
        if m:
            stats.health.technology = m.group(1).strip()

    @staticmethod
    def _parse_sysfs(ls, stats):
        """Parse sysfs battery data from bugreport."""
        RealmeParser._parse_sysfs(ls, stats)  # Same sysfs format

    @staticmethod
    def _parse_mi_props(ls, stats):
        """Parse Xiaomi system properties."""
        m = re.search(r"\[ro\.product\.model\]:\s*\[(.+?)\]", ls)
        if m and stats.device.model == "Unknown":
            stats.device.model = f"Xiaomi ({m.group(1)})"
        m = re.search(r"\[ro\.build\.display\.id\]:\s*\[(.+?)\]", ls)
        if m:
            stats.device.build = m.group(1)
        m = re.search(r"\[ro\.miui\.ui\.version\.name\]:\s*\[(.+?)\]", ls)
        if m:
            stats.device.build_date = f"MIUI {m.group(1)}"
        m = re.search(r"\[ro\.product\.vendor\.device\]:\s*\[(.+?)\]", ls)
        if m:
            stats.device.model_code = m.group(1)



class VivoParser:
    """Parser for iQOO/Vivo bugreports and diagnostic data.
    
    How to get battery data on iQOO/Vivo:
    1. Dial *#*#556688#*#* for Factory Test
    2. Or: adb bugreport
    3. Or: Settings → Battery → Battery Health
    """

    @staticmethod
    def can_parse(file_path: str, first_lines: str) -> bool:
        indicators = ["iqoo", "IQOO", "vivo", "VIVO", "Vivo", 
                       "funtouch", "Funtouch", "originos", "OriginOS"]
        return any(ind in first_lines for ind in indicators)

    @staticmethod
    def parse(file_path: str, stats: BatteryStats):
        stats.parser_brand = "iQOO/Vivo"
        stats.device.brand = "iQOO/Vivo"
        XiaomiParser.parse(file_path, stats)  # Same sysfs format

class GenericParser:
    """Generic parser for any Android bugreport or dumpstate file.

    Works with:
    - adb bugreport output
    - Any dumpstate file
    - Standard Android battery dumps

    How to get a bugreport on any Android:
    1. Enable Developer Options (tap Build Number 7 times)
    2. Settings → Developer Options → Take Bug Report
    3. Or: adb bugreport
    """

    @staticmethod
    def can_parse(file_path: str, first_lines: str) -> bool:
        # Generic parser is the fallback — always returns True
        return True

    @staticmethod
    def parse(file_path: str, stats: BatteryStats):
        stats.parser_brand = "Generic Android"
        stats.device.brand = "Android"

        with open(file_path, "r", errors="replace") as f:
            for line in f:
                ls = line.strip()
                GenericParser._parse_standard(ls, stats)
                GenericParser._parse_dumpsys(ls, stats)
                GenericParser._parse_kernel(ls, stats)

    @staticmethod
    def _parse_standard(ls, stats):
        # Device info
        m = re.search(r'Build fingerprint:\s*[\'"]?(.+?)[\'"]?\s*$', ls)
        if m:
            fp = m.group(1)
            parts = fp.split("/")
            if len(parts) >= 2:
                stats.device.model_code = parts[1]
            m2 = re.search(r":(\d+)/", fp)
            if m2:
                stats.device.android_version = m2.group(1)

        m = re.search(r"Build:\s*(.+)", ls)
        if m:
            stats.device.build = m.group(1).strip()

        m = re.search(r"Network:\s*(.+)", ls)
        if m:
            stats.device.network = m.group(1).strip()

    @staticmethod
    def _parse_dumpsys(ls, stats):
        m = re.search(r"level:\s*(\d+)", ls)
        if m:
            stats.battery_level = int(m.group(1))

        m = re.search(r"health:\s*(\d+)", ls)
        if m and not stats.health.health_status:
            health_val = int(m.group(1))
            health_map = {
                2: "Good",
                3: "Overheat",
                4: "Dead",
                5: "Over Voltage",
                6: "Failure",
                7: "Cold",
            }
            stats.health.health_status = health_map.get(
                health_val, f"Code {health_val}"
            )

        m = re.search(r"temperature:\s*(\d+)", ls)
        if m and stats.health.max_temp_c is None:
            stats.health.max_temp_c = int(m.group(1)) / 10.0

        m = re.search(r"voltage:\s*(\d+)", ls)
        if m and stats.health.current_voltage_mv is None:
            stats.health.current_voltage_mv = int(m.group(1))

        m = re.search(r"technology:\s*(.+)", ls)
        if m:
            stats.health.technology = m.group(1).strip()

        # Battery capacity from dumpsys
        m = re.search(r"Estimated battery capacity:\s*(\d+)", ls)
        if m and stats.health.design_capacity_mah is None:
            stats.health.design_capacity_mah = int(m.group(1))

        m = re.search(r"Min learned battery capacity:\s*(\d+)", ls)
        if m and stats.health.full_charge_capacity_mah is None:
            stats.health.full_charge_capacity_mah = int(m.group(1))

        m = re.search(r"Max learned battery capacity:\s*(\d+)", ls)
        if m and stats.health.full_charge_capacity_mah is None:
            stats.health.full_charge_capacity_mah = int(m.group(1))

        # Cycle count from batterystats
        m = re.search(r"Estimated battery cycle count:\s*(\d+)", ls)
        if m and stats.health.cycle_count is None:
            stats.health.cycle_count = int(m.group(1))

    @staticmethod
    def _parse_kernel(ls, stats):
        # /sys/class/power_supply/battery/ data
        GenericParser._parse_sysfs(ls, stats)

    @staticmethod
    def _parse_sysfs(ls, stats):
        for pattern, attr in [
            (r"POWER_SUPPLY_CYCLE_COUNT=(\d+)", "cycle_count"),
            (r"POWER_SUPPLY_CHARGE_FULL=(\d+)", "charge_full"),
            (r"POWER_SUPPLY_CHARGE_FULL_DESIGN=(\d+)", "charge_full_design"),
            (r"POWER_SUPPLY_TEMP=(\d+)", "temp"),
            (r"POWER_SUPPLY_VOLTAGE_NOW=(\d+)", "voltage"),
        ]:
            m = re.search(pattern, ls)
            if m:
                val = int(m.group(1))
                if attr == "cycle_count" and stats.health.cycle_count is None:
                    stats.health.cycle_count = val
                elif (
                    attr == "charge_full"
                    and stats.health.full_charge_capacity_mah is None
                ):
                    stats.health.full_charge_capacity_mah = val // 1000
                elif (
                    attr == "charge_full_design"
                    and stats.health.design_capacity_mah is None
                ):
                    stats.health.design_capacity_mah = val // 1000
                elif attr == "temp" and stats.health.max_temp_c is None:
                    stats.health.max_temp_c = val / 10.0
                elif attr == "voltage" and stats.health.current_voltage_mv is None:
                    stats.health.current_voltage_mv = val // 1000


# ─── Parser Registry ────────────────────────────────────────────────────────

PARSERS = [("vivo", VivoParser),
    ("samsung", SamsungParser),
    ("realme", RealmeParser),
    ("xiaomi", XiaomiParser),
    ("generic", GenericParser),
]


def detect_brand(file_path: str) -> str:
    """Auto-detect the brand from file content."""
    try:
        with open(file_path, "r", errors="replace") as f:
            first_chunk = ""
            for i, line in enumerate(f):
                first_chunk += line
                if i > 50:
                    break
            for name, parser in PARSERS:
                if name != "generic" and parser.can_parse(file_path, first_chunk):
                    return name
    except Exception:
        pass
    return "generic"


def get_parser(brand: str):
    """Get parser by brand name."""
    for name, parser in PARSERS:
        if name == brand:
            return parser
    return GenericParser


def parse_file(file_path: str, brand: str = "auto") -> BatteryStats:
    """Parse a file and return battery stats."""
    stats = BatteryStats()
    stats.file_name = os.path.basename(file_path)
    stats.file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    # Handle zip files (bugreport zips)
    if file_path.endswith(".zip"):
        file_path = _extract_from_zip(file_path)
        if not file_path:
            return stats

    # Detect brand if auto
    if brand == "auto":
        brand = detect_brand(file_path)

    parser = get_parser(brand)
    parser.parse(file_path, stats)

    # Derive model from build if not set
    if stats.device.model == "Unknown" and stats.device.build:
        _derive_model(stats)

    return stats


def _extract_from_zip(zip_path: str) -> Optional[str]:
    """Extract bugreport text from a zip file."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Look for bugreport text files
            for name in zf.namelist():
                if "bugreport" in name.lower() and name.endswith(".txt"):
                    # Extract to temp
                    tmp = tempfile.NamedTemporaryFile(
                        mode="w", suffix=".txt", delete=False
                    )
                    with zf.open(name) as src:
                        tmp.write(src.read().decode("utf-8", errors="replace"))
                    tmp.close()
                    return tmp.name
                elif "bugreport" in name.lower() and name.endswith(".log"):
                    tmp = tempfile.NamedTemporaryFile(
                        mode="w", suffix=".log", delete=False
                    )
                    with zf.open(name) as src:
                        tmp.write(src.read().decode("utf-8", errors="replace"))
                    tmp.close()
                    return tmp.name
            # Fallback: try any large text file
            for name in zf.namelist():
                if (
                    name.endswith((".txt", ".log"))
                    and zf.getinfo(name).file_size > 100000
                ):
                    tmp = tempfile.NamedTemporaryFile(
                        mode="w", suffix=".txt", delete=False
                    )
                    with zf.open(name) as src:
                        tmp.write(src.read().decode("utf-8", errors="replace"))
                    tmp.close()
                    return tmp.name
    except Exception as e:
        print(f"⚠️  Error extracting zip: {e}")
    return None


def _derive_model(stats: BatteryStats):
    build = stats.device.build
    if "S921" in build:
        stats.device.model = "Samsung Galaxy S24"
    elif "S926" in build:
        stats.device.model = "Samsung Galaxy S25"
    elif "S928" in build:
        stats.device.model = "Samsung Galaxy S25 Ultra"
    elif "A315" in build:
        stats.device.model = "Samsung Galaxy A31"
    elif "A54" in build:
        stats.device.model = "Samsung Galaxy A54"
    elif "A55" in build:
        stats.device.model = "Samsung Galaxy A55"
    elif "A34" in build:
        stats.device.model = "Samsung Galaxy A34"
    elif "A15" in build:
        stats.device.model = "Samsung Galaxy A15"
    elif "A25" in build:
        stats.device.model = "Samsung Galaxy A25"
    elif "Pixel" in build or "google" in build.lower():
        stats.device.model = f"Google ({stats.device.model_code})"
    else:
        stats.device.model = f"{stats.device.brand} ({stats.device.model_code})"


# ─── Metrics Calculator ─────────────────────────────────────────────────────


def calculate_metrics(stats: BatteryStats) -> dict:
    m = {}

    if stats.health.cycle_count is not None:
        m["cycle_count"] = float(stats.health.cycle_count)
    if stats.health.asoc is not None:
        m["asoc_percent"] = stats.health.asoc
    elif stats.health.full_charge_capacity_mah and stats.health.design_capacity_mah:
        m["asoc_percent"] = round(
            stats.health.full_charge_capacity_mah
            / stats.health.design_capacity_mah
            * 100
        )
    if stats.health.bsoh is not None:
        m["bsoh_percent"] = stats.health.bsoh
    if stats.health.max_temp_c is not None:
        m["max_temp_c"] = stats.health.max_temp_c
    if stats.health.max_current_ma is not None:
        m["max_current_ma"] = stats.health.max_current_ma
    if stats.health.design_capacity_mah:
        m["design_capacity_mah"] = stats.health.design_capacity_mah
    if stats.health.full_charge_capacity_mah:
        m["effective_capacity_mah"] = stats.health.full_charge_capacity_mah
    elif "asoc_percent" in m and "design_capacity_mah" in m:
        m["effective_capacity_mah"] = round(
            m["design_capacity_mah"] * m["asoc_percent"] / 100
        )

    # Snapshots
    if stats.snapshots:
        temps = [s.temp_c for s in stats.snapshots if s.temp_c]
        if temps:
            m["avg_temp_c"] = round(sum(temps) / len(temps), 1)
            m["min_temp_c"] = min(temps)
            m["max_snapshot_temp_c"] = max(temps)
        voltages = [s.voltage_mv for s in stats.snapshots if s.voltage_mv]
        if voltages:
            m["avg_voltage_mv"] = round(sum(voltages) / len(voltages))
        currents = [s.current_ma for s in stats.snapshots if s.current_ma is not None]
        if currents:
            m["avg_current_ma"] = round(sum(currents) / len(currents))
            m["max_discharge_ma"] = min(currents)
            m["max_charge_ma"] = max(currents)
        m["snapshot_count"] = len(stats.snapshots)

    # Health grade
    asoc = m.get("asoc_percent")
    if asoc is not None:
        if asoc >= 95:
            m["health_grade"], m["health_emoji"] = "Excellent", "🟢"
        elif asoc >= 85:
            m["health_grade"], m["health_emoji"] = "Good", "🟡"
        elif asoc >= 70:
            m["health_grade"], m["health_emoji"] = "Fair", "🟠"
        else:
            m["health_grade"], m["health_emoji"] = "Poor", "🔴"

    # Predictions
    cycles = m.get("cycle_count", 0)
    health = m.get("asoc_percent", 100)
    if cycles > 0 and health < 100:
        deg_per_cycle = (100 - health) / cycles
        m["degradation_per_cycle"] = round(deg_per_cycle, 4)
        if health > 80:
            cycles_to_80 = (health - 80) / deg_per_cycle
            m["cycles_to_80"] = int(cycles_to_80)
            days_used = cycles / 0.92
            m["est_days_used"] = int(days_used)
            m["est_years_used"] = round(days_used / 365, 1)
            remaining_days = cycles_to_80 / 0.92
            m["est_remaining_days"] = int(remaining_days)
            m["est_remaining_months"] = int(remaining_days / 30)

    # Max temp warning
    max_t = m.get("max_temp_c", 0)
    if max_t > 70:
        m["temp_warning"] = "🔴 CRITICAL: >70°C — battery damage likely"
    elif max_t > 60:
        m["temp_warning"] = "🟠 WARNING: >60°C — avoid charging while gaming"
    elif max_t > 45:
        m["temp_warning"] = "🟡 NOTICE: >45°C — normal for heavy use"

    return m


# ─── Report Formatters ──────────────────────────────────────────────────────


def format_report(stats: BatteryStats, metrics: dict) -> str:
    lines = []
    d = stats.device
    h = stats.health

    lines.append("=" * 60)
    lines.append("  🔋 BATTERY HEALTH REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Brand:         {d.brand}")
    lines.append(f"  Device:        {d.model}")
    if d.model_code:
        lines.append(f"  Model Code:    {d.model_code}")
    if d.android_version:
        lines.append(f"  Android:       {d.android_version}")
    if d.build:
        lines.append(f"  Build:         {d.build}")
    if d.build_date:
        lines.append(f"  Build Date:    {d.build_date}")
    if d.network:
        lines.append(f"  Network:       {d.network}")
    if d.first_use_date:
        lines.append(f"  First Use:     {d.first_use_date}")
    if d.screen_manufacture_date:
        lines.append(f"  Screen Made:   {d.screen_manufacture_date}")
    lines.append(f"  Parser:        {stats.parser_brand}")
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
    if h.health_status:
        lines.append(f"  Health Status:     {h.health_status}")
    if "cycle_count" in metrics:
        lines.append(f"  Cycle Count:       {metrics['cycle_count']:.0f}")
    if "design_capacity_mah" in metrics:
        lines.append(f"  Design Capacity:   {metrics['design_capacity_mah']} mAh")
    if "effective_capacity_mah" in metrics:
        lines.append(f"  Effective Cap:     {metrics['effective_capacity_mah']} mAh")
    if h.technology:
        lines.append(f"  Technology:        {h.technology}")
    if h.charge_status:
        lines.append(f"  Charge Status:     {h.charge_status}")
    if "max_temp_c" in metrics:
        warn = " ⚠️" if metrics["max_temp_c"] > 60 else ""
        lines.append(f"  Max Temp:          {metrics['max_temp_c']}°C{warn}")
    if "max_current_ma" in metrics:
        lines.append(f"  Max Current:       {metrics['max_current_ma']} mA")
    if stats.battery_level is not None:
        lines.append(f"  Current Level:     {stats.battery_level}%")

    if stats.snapshots:
        lines.append("")
        lines.append("-" * 60)
        lines.append("  ⚡ SNAPSHOT DATA")
        lines.append("-" * 60)
        if "snapshot_count" in metrics:
            lines.append(f"  Snapshots:      {metrics['snapshot_count']}")
        if "avg_voltage_mv" in metrics:
            lines.append(f"  Avg Voltage:    {metrics['avg_voltage_mv']} mV")
        if "avg_current_ma" in metrics:
            lines.append(f"  Avg Current:    {metrics['avg_current_ma']} mA")
        if "avg_temp_c" in metrics:
            lines.append(f"  Avg Temp:       {metrics['avg_temp_c']}°C")

    # Apps
    cs = stats.charge_session
    if cs.apps:
        lines.append("")
        lines.append("-" * 60)
        lines.append("  📱 TOP BATTERY DRAINERS")
        lines.append("-" * 60)
        lines.append(f"  {'Rank':<5} {'App':<40} {'mAh':>8} {'%':>6}")
        lines.append("  " + "-" * 59)
        for i, app in enumerate(cs.apps[:15], 1):
            pkg = app.package.split(".")[-1] if "." in app.package else app.package
            lines.append(
                f"  {i:<5} {pkg:<40} {app.usage_mah:>7.1f} {app.usage_percent:>5.1f}%"
            )

    # Predictions
    lines.append("")
    lines.append("-" * 60)
    lines.append("  🔮 PREDICTIONS & INSIGHTS")
    lines.append("-" * 60)

    if "cycles_to_80" in metrics:
        lines.append(f"  Cycles to 80%:     ~{metrics['cycles_to_80']}")
    if "est_days_used" in metrics:
        lines.append(
            f"  Est. Days Used:    ~{metrics['est_days_used']} ({metrics['est_years_used']} years)"
        )
    if "est_remaining_months" in metrics:
        lines.append(f"  Est. Remaining:    ~{metrics['est_remaining_months']} months")
    if "degradation_per_cycle" in metrics:
        lines.append(
            f"  Degradation/Cycle: {metrics['degradation_per_cycle'] * 100:.3f}%"
        )
    if "temp_warning" in metrics:
        lines.append(f"\n  {metrics['temp_warning']}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_comparison(all_stats, all_metrics):
    lines = ["", "=" * 70, "  📱 DEVICE COMPARISON", "=" * 70, ""]
    header = f"  {'Metric':<22}"
    for s in all_stats:
        header += f" {s.device.model[:20]:>20}"
    lines.append(header)
    lines.append("  " + "-" * (22 + 22 * len(all_stats)))

    for label, getter in [
        ("Brand", lambda m, s: s.device.brand[:20]),
        ("ASOC", lambda m, s: f"{m.get('asoc_percent', 'N/A')}%"),
        ("Cycles", lambda m, s: f"{m.get('cycle_count', 'N/A')}"),
        ("Max Temp", lambda m, s: f"{m.get('max_temp_c', 'N/A')}°C"),
        ("Design Cap", lambda m, s: f"{m.get('design_capacity_mah', 'N/A')}"),
        (
            "Health",
            lambda m, s: f"{m.get('health_emoji', '')} {m.get('health_grade', 'N/A')}",
        ),
        ("Remaining", lambda m, s: f"{m.get('est_remaining_months', 'N/A')} mo"),
    ]:
        row = f"  {label:<22}"
        for metrics, stats in zip(all_metrics, all_stats):
            row += f" {str(getter(metrics, stats)):>20}"
        lines.append(row)

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


# ─── Main ───────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    files = []
    json_mode = False
    compare_mode = False
    csv_mode = False
    chart_mode = False
    score_mode = False
    history_mode = False
    adb_mode = False
    brand = "auto"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--json":
            json_mode = True
        elif args[i] == "--compare":
            compare_mode = True
        elif args[i] == "--csv":
            csv_mode = True
        elif args[i] == "--chart":
            chart_mode = True
        elif args[i] == "--score":
            score_mode = True
        elif args[i] == "--history":
            history_mode = True
        elif args[i] == "--adb":
            adb_mode = True
        elif args[i] == "--brand" and i + 1 < len(args):
            brand = args[i + 1].lower()
            i += 1
        elif os.path.exists(args[i]):
            files.append(args[i])
        else:
            print(f"⚠️  File not found: {args[i]}")
        i += 1

    if adb_mode:
        print_adb_guide()
        return

    if not files:
        print("❌ No valid files provided.")
        sys.exit(1)

    all_stats = []
    all_metrics = []

    for fp in files:
        if not json_mode:
            print(f"🔍 Parsing: {os.path.basename(fp)}...")
        stats = parse_file(fp, brand)
        metrics = calculate_metrics(stats)
        all_stats.append(stats)
        all_metrics.append(metrics)
        if not json_mode:
            print(format_report(stats, metrics))

    if json_mode:
        output = []
        for s, m in zip(all_stats, all_metrics):
            entry = {
                "device": asdict(s.device),
                "health": asdict(s.health),
                "metrics": m,
                "snapshot_count": len(s.snapshots),
                "parser": s.parser_brand,
                "file": s.file_name,
                "file_size_mb": round(s.file_size_mb, 1),
            }
            if s.charge_session.apps:
                entry["top_apps"] = [
                    {
                        "package": a.package,
                        "mah": a.usage_mah,
                        "percent": a.usage_percent,
                    }
                    for a in s.charge_session.apps[:10]
                ]
            output.append(entry)
        print(json.dumps(output, indent=2))

    if compare_mode and len(all_stats) > 1:
        print(format_comparison(all_stats, all_metrics))

    if csv_mode:
        output_csv(all_stats, all_metrics)

    if chart_mode:
        for s, m in zip(all_stats, all_metrics):
            print(format_degradation_chart(s, m))

    if score_mode:
        for s, m in zip(all_stats, all_metrics):
            print(format_battery_score(s, m))

    if history_mode:
        for s, m in zip(all_stats, all_metrics):
            save_history(s, m)
        print(f"\n📁 History saved to .battery_history.json")

    if adb_mode:
        print_adb_guide()


# ─── New Features ───────────────────────────────────────────────────────────


def format_degradation_chart(stats: BatteryStats, metrics: dict) -> str:
    """ASCII chart showing battery degradation over cycles."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  📉 BATTERY DEGRADATION CURVE")
    lines.append("=" * 60)
    lines.append("")

    cycles = metrics.get("cycle_count", 0)
    asoc = metrics.get("asoc_percent", 100)
    deg = metrics.get("degradation_per_cycle", 0)

    if cycles == 0 or deg == 0:
        lines.append("  Not enough data for degradation chart.")
        return "\n".join(lines)

    chart_height = 12
    chart_width = 40
    max_cycles = int(cycles * 1.5)

    lines.append(f"  {stats.device.model}")
    lines.append(f"  Current: {cycles:.0f} cycles @ {asoc}% health")
    lines.append("")

    for row in range(chart_height, -1, -1):
        health_at_row = 50 + (row / chart_height) * 50
        label = f"  {health_at_row:>3.0f}% │"
        bar = ""
        for col in range(chart_width):
            cycle_at_col = (col / chart_width) * max_cycles
            health_at_col = 100 - (deg * cycle_at_col)
            if health_at_col >= health_at_row and cycle_at_col <= cycles:
                bar += "█"
            elif cycle_at_col <= cycles:
                bar += "░"
            else:
                bar += " "
        lines.append(f"{label}{bar}")

    lines.append(f"       └{'─' * chart_width}")
    mid = max_cycles // 2
    lines.append(
        f"        0{' ' * (chart_width // 2 - 3)}{mid} cycles{' ' * (chart_width // 2 - 8)}{max_cycles}"
    )
    lines.append("")

    if deg > 0:
        lines.append("  📌 Key Milestones:")
        lines.append(f"     90% health: ~{int((100 - 90) / deg)} cycles")
        lines.append(
            f"     80% health: ~{int((100 - 80) / deg)} cycles (replace threshold)"
        )
        lines.append(f"     70% health: ~{int((100 - 70) / deg)} cycles")
        lines.append(f"     Current:    ~{int(cycles)} cycles @ {asoc}%")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_battery_score(stats: BatteryStats, metrics: dict) -> str:
    """Calculate a composite battery score (0-100)."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  🏆 BATTERY SCORE")
    lines.append("=" * 60)
    lines.append("")

    scores = {}
    asoc = metrics.get("asoc_percent", 50)
    scores["Health (ASOC)"] = min(asoc, 100)

    cycles = metrics.get("cycle_count", 500)
    if cycles < 100:
        scores["Cycle Wear"] = 100
    elif cycles < 300:
        scores["Cycle Wear"] = 90
    elif cycles < 500:
        scores["Cycle Wear"] = 80
    elif cycles < 800:
        scores["Cycle Wear"] = 70
    elif cycles < 1200:
        scores["Cycle Wear"] = 60
    elif cycles < 1500:
        scores["Cycle Wear"] = 50
    else:
        scores["Cycle Wear"] = max(100 - (cycles - 1500) / 50, 10)

    max_temp = metrics.get("max_temp_c", 40)
    if max_temp < 40:
        scores["Thermal"] = 100
    elif max_temp < 45:
        scores["Thermal"] = 90
    elif max_temp < 50:
        scores["Thermal"] = 80
    elif max_temp < 55:
        scores["Thermal"] = 70
    elif max_temp < 60:
        scores["Thermal"] = 60
    elif max_temp < 70:
        scores["Thermal"] = 40
    else:
        scores["Thermal"] = max(100 - (max_temp - 70) * 5, 5)

    design = metrics.get("design_capacity_mah", 4000)
    effective = metrics.get("effective_capacity_mah", design)
    if design > 0:
        scores["Capacity"] = min(effective / design * 100, 100)
    else:
        scores["Capacity"] = 50

    weights = {
        "Health (ASOC)": 0.40,
        "Cycle Wear": 0.25,
        "Thermal": 0.20,
        "Capacity": 0.15,
    }
    total_score = round(sum(scores[k] * weights[k] for k in scores), 1)

    if total_score >= 90:
        grade, emoji = "S", "🏆"
    elif total_score >= 80:
        grade, emoji = "A", "🟢"
    elif total_score >= 70:
        grade, emoji = "B", "🟡"
    elif total_score >= 60:
        grade, emoji = "C", "🟠"
    elif total_score >= 50:
        grade, emoji = "D", "🔴"
    else:
        grade, emoji = "F", "💀"

    lines.append(f"  {stats.device.model}")
    lines.append("")
    lines.append(f"  Overall Score:  {total_score}/100  {emoji} Grade: {grade}")
    lines.append("")

    for name, score in scores.items():
        bar_len = int(score / 100 * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        lines.append(f"  {name:<15} {bar} {score:.0f}")

    lines.append("")
    lines.append("  💬 Verdict:")
    if total_score >= 90:
        lines.append("     Excellent condition. No action needed.")
    elif total_score >= 80:
        lines.append("     Healthy. Continue normal usage.")
    elif total_score >= 70:
        lines.append("     Aging. Monitor temperature and charging habits.")
    elif total_score >= 60:
        lines.append("     Showing wear. Consider replacing within 6 months.")
    elif total_score >= 50:
        lines.append("     Degraded. Replacement recommended.")
    else:
        lines.append("     End of life. Replace immediately.")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def output_csv(all_stats: list, all_metrics: list):
    """Output CSV for spreadsheet analysis."""
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    headers = [
        "Brand",
        "Model",
        "Android",
        "ASOC%",
        "BSOH%",
        "Cycles",
        "Design_mAh",
        "Effective_mAh",
        "MaxTemp_C",
        "MaxCurrent_mA",
        "HealthStatus",
        "DegPerCycle%",
        "CyclesTo80",
        "RemainingMonths",
        "File",
        "Size_MB",
    ]
    writer.writerow(headers)
    for s, m in zip(all_stats, all_metrics):
        writer.writerow(
            [
                s.device.brand,
                s.device.model,
                s.device.android_version,
                m.get("asoc_percent", ""),
                m.get("bsoh_percent", ""),
                m.get("cycle_count", ""),
                m.get("design_capacity_mah", ""),
                m.get("effective_capacity_mah", ""),
                m.get("max_temp_c", ""),
                m.get("max_current_ma", ""),
                s.health.health_status,
                m.get("degradation_per_cycle", ""),
                m.get("cycles_to_80", ""),
                m.get("est_remaining_months", ""),
                s.file_name,
                round(s.file_size_mb, 1),
            ]
        )
    csv_str = buf.getvalue()
    print(csv_str)
    with open("battery_export.csv", "w") as f:
        f.write(csv_str)
    print("📁 CSV saved to battery_export.csv")


def save_history(stats: BatteryStats, metrics: dict):
    """Save snapshot to history for tracking over time."""
    history_path = ".battery_history.json"
    history = []
    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            try:
                history = json.load(f)
            except:
                history = []
    entry = {
        "timestamp": datetime.now().isoformat(),
        "device": stats.device.model,
        "brand": stats.device.brand,
        "asoc": metrics.get("asoc_percent"),
        "cycles": metrics.get("cycle_count"),
        "max_temp": metrics.get("max_temp_c"),
        "design_mah": metrics.get("design_capacity_mah"),
        "effective_mah": metrics.get("effective_capacity_mah"),
        "health_grade": metrics.get("health_grade"),
        "file": stats.file_name,
    }
    history.append(entry)
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)


def print_adb_guide():
    """Print universal ADB commands for battery data."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  📱 UNIVERSAL ADB BATTERY COMMANDS                          ║
║  Works on ANY Android phone with USB debugging enabled       ║
╚══════════════════════════════════════════════════════════════╝

  SETUP:
    1. Enable Developer Options (tap Build Number 7 times)
    2. Enable USB Debugging in Developer Options
    3. Connect phone to PC via USB
    4. Accept "Allow USB debugging" on phone

  QUICK BATTERY INFO:
    adb shell dumpsys battery

  FULL BATTERY STATS:
    adb shell dumpsys batterystats > battery_stats.txt

  COMPLETE BUGREPORT (recommended):
    adb bugreport > bugreport.txt

  KERNEL BATTERY DATA:
    adb shell cat /sys/class/power_supply/battery/cycle_count
    adb shell cat /sys/class/power_supply/battery/charge_full
    adb shell cat /sys/class/power_supply/battery/charge_full_design
    adb shell cat /sys/class/power_supply/battery/temp
    adb shell cat /sys/class/power_supply/battery/voltage_now

  BRAND-SPECIFIC (opens diagnostic menu):
    Samsung:    adb shell am start -a android.intent.action.DIAL -d tel:*%239900%23
    Xiaomi:     adb shell am start -a android.intent.action.DIAL -d tel:*%23*%23284%23*%23*
    Realme:     adb shell am start -a android.intent.action.DIAL -d tel:*%23800%23

  BATTERY HISTORY TRACKING:
    adb shell dumpsys batterystats --reset    # reset counters
    ... use phone normally ...
    adb bugreport > bugreport.zip

  THEN ANALYZE:
    python3 battery_analyzer.py bugreport.txt
    python3 battery_analyzer.py bugreport.txt --score
    python3 battery_analyzer.py bugreport.txt --chart
    python3 battery_analyzer.py bugreport.txt --csv
    python3 battery_analyzer.py bugreport.txt --history

╚══════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    main()
