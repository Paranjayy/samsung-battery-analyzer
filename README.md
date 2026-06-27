# Samsung Battery Analyzer 🔋

Parse Samsung dumpstate logs and extract battery health data. Works with `*#9900#` SysDump logs.

## What it extracts

- **Battery ASOC** (Actual State of Charge) - the real health %
- **BSOH** (Battery State of Health)
- **Cycle count** - how many full charge cycles
- **Max temp & current** ever recorded
- **Live voltage/current/temp** snapshots from kernel logs
- **Health grade** with color-coded emoji
- **Predictions** - estimated remaining life, cycles to 80%

## Usage

```bash
# Single device report
python3 battery_analyzer.py dumpstate.txt

# Compare two devices
python3 battery_analyzer.py phone1.txt phone2.log --compare

# JSON output (for piping/processing)
python3 battery_analyzer.py dumpstate.txt --json
```

## Supported files

Any Samsung dumpstate file from:
- `*#9900#` → Run dumpstate → SD card
- Samsung device diagnostic logs
- Both `.txt` and `.log` extensions

## Tested on

- Samsung Galaxy A31 (Android 12, OneUI 3.x)
- Samsung Galaxy S24 (Android 16, OneUI 8.x)

## How Samsung battery data works

| Field | Location | Meaning |
|-------|----------|---------|
| `mSavedBatteryAsoc` | DUMP OF SERVICE battery | Battery health % |
| `mSavedBatteryUsage` | DUMP OF SERVICE battery | Cycle count (÷100) |
| `mSavedBatteryMaxTemp` | DUMP OF SERVICE battery | Max temp ever (÷10 = °C) |
| `mSavedBatteryMaxCurrent` | DUMP OF SERVICE battery | Max current draw (mA) |
| `mSavedBatteryBsoh` | DUMP OF SERVICE battery | Battery SOH % |
| `sec_bat_monitor_work` | Kernel log | Live cycle count |
| `sec_bat_get_battery_info` | Kernel log | Voltage, current, SOC, temp |

## References

- [MyBattery](https://github.com/Alyaqdhans/MyBattery) - Android app for Samsung battery health
- [samsung-batterystats](https://github.com/dogpoopy/samsung-batterystats) - Battery stats viewer
