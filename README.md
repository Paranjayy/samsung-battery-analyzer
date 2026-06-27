# Universal Battery Analyzer 🔋

Parse battery health data from **Samsung, Realme/Oppo/OnePlus, Xiaomi/Redmi/POCO**, iPhone, iPad, and any Android bugreport. Works with dumpstate logs, bugreport zips, and kernel logs.

> 📖 **[Full Device Guide](DEVICE_GUIDE.md)** — How to get battery data from ANY phone/tablet (Android + iOS)

## Supported Brands

| Brand | Diagnostic Code | Data Source |
|-------|----------------|-------------|
| **Samsung** | `*#9900#` | SysDump → `dumpState_*.log` |
| **Realme/Oppo** | `*#800#` | Logkit → bugreport |
| **OnePlus** | `*#800#` | Logkit → bugreport |
| **Xiaomi/Redmi** | `*#*#284#*#*` | Bugreport → `bugreport-*.zip` |
| **POCO** | `*#*#284#*#*` | Bugreport → `bugreport-*.zip` |
| **Google Pixel** | `*#*#284#*#*` | Bugreport → `bugreport-*.zip` |
| **Any Android** | `adb bugreport` | Standard Android bugreport |

## What it extracts

- **ASOC** (Actual State of Charge) — real battery health %
- **BSOH** (Battery State of Health) — overall condition
- **Cycle count** — full charge cycles
- **Design vs Effective capacity** — how much capacity is left
- **Max temperature** — ever recorded (with danger warnings)
- **App battery drain** — which apps use the most power
- **Health grade** with color-coded emoji
- **Lifespan predictions** — estimated remaining life

## Usage

```bash
# Auto-detect brand
python3 battery_analyzer.py dumpstate.txt

# Force brand parser
python3 battery_analyzer.py bugreport.txt --brand xiaomi
python3 battery_analyzer.py oplus_log.txt --brand realme

# Compare two phones
python3 battery_analyzer.py phone1.txt phone2.log --compare

# JSON output (for scripting/apps)
python3 battery_analyzer.py dumpstate.txt --json

# Parse bugreport zip
python3 battery_analyzer.py bugreport-samsung-2026.zip
```

## How to get battery data

### Samsung
1. Dial `*#9900#` → Run dumpstate → OK → Copy to SD card
2. Find `dumpState_*.log` in `/sdcard/log/`

### Realme/Oppo/OnePlus
1. Dial `*#800#` → Start Record → Use phone → Stop Record
2. Find zip in `/sdcard/LogKit/`
3. Or: `adb bugreport`

### Xiaomi/Redmi/POCO
1. Dial `*#*#284#*#*` for bug report
2. Or: Settings → About Phone → tap MIUI version 7x → Developer Options → Take Bug Report
3. Or: `adb bugreport`

### Any Android
1. Enable Developer Options (tap Build Number 7 times)
2. Settings → Developer Options → Take Bug Report
3. Or: `adb bugreport > bugreport.txt`

## What each field means

| Field | Samsung Field | Standard Field | Meaning |
|-------|--------------|----------------|---------|
| ASOC | `mSavedBatteryAsoc` | `charge_full / charge_full_design * 100` | Battery health % |
| Cycles | `mSavedBatteryUsage ÷ 100` | `POWER_SUPPLY_CYCLE_COUNT` | Full charge cycles |
| Max Temp | `mSavedBatteryMaxTemp ÷ 10` | `POWER_SUPPLY_TEMP ÷ 10` | Hottest ever (°C) |
| Design Cap | `efs_buf[3]` | `POWER_SUPPLY_CHARGE_FULL_DESIGN` | Original capacity |
| Effective Cap | `efs_buf[4]` | `POWER_SUPPLY_CHARGE_FULL` | Current capacity |

## Battery Health Grades

| Grade | Emoji | ASOC Range | What it means |
|-------|-------|------------|---------------|
| Excellent | 🟢 | 95-100% | Like new |
| Good | 🟡 | 85-94% | Normal wear |
| Fair | 🟠 | 70-84% | Getting old |
| Poor | 🔴 | <70% | Consider replacing |

## Files

```
battery-analyzer/
├── battery_analyzer.py          # Main tool (single file, no deps)
├── README.md                    # This file
├── .gitignore                   # Excludes large log files
└── reports/                     # Sample analysis reports
    ├── KP-A31-Battery-Report.md
    └── Pujit-S24-Battery-Report.md
```

## Requirements

- Python 3.6+
- No external dependencies (pure stdlib)

## References

**Android:**
- [MyBattery](https://github.com/Alyaqdhans/MyBattery) — Samsung battery health app
- [samsung-batterystats](https://github.com/dogpoopy/samsung-batterystats) — Samsung battery stats viewer
- [AccuBattery](https://play.google.com/store/apps/details?id=com.digibites.accubattery) — Popular battery monitor

**iOS/iPad:**
- [CoconutBattery](https://coconut-flavor.com/coconutbattery/) — Mac app for detailed battery analysis
- [3uTools](https://www.3u.com/) — Windows tool for iPhone/iPad battery info
- [PowerUtil Shortcut](https://www.icloud.com/shortcuts/) — Extract cycle count from analytics
