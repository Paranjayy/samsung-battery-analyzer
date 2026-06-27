# 📱 Device Guide — How to Get Battery Data From Any Device

Complete guide for extracting battery health data from Samsung, Realme, Xiaomi, iPhone, iPad, and more.

---

## 🟦 Android Phones

### Samsung (`*#9900#`)
1. Open Phone app → Dial `*#9900#`
2. Tap **"Run dumpstate/logcat"** → Wait 2-3 min → OK
3. Tap **"Copy to SD card"** (or internal storage)
4. Find file: `/sdcard/log/dumpState_*.log`
5. Share to PC via USB/Telegram/email

**Direct analysis:**
```bash
python3 battery_analyzer.py dumpState_*.log
```

---

### Realme / Oppo / OnePlus (`*#800#`)
1. Open Phone app → Dial `*#800#`
2. Tap **"Start Record"** → Use phone for 2-3 minutes
3. Tap **"Stop Record"**
4. Find zip in: `/sdcard/LogKit/`
5. Share the zip file

**Direct analysis:**
```bash
python3 battery_analyzer.py com.coloros.zip --brand realme
```

**Alternative (no dial code):**
```bash
adb bugreport > bugreport.txt
python3 battery_analyzer.py bugreport.txt
```

---

### Xiaomi / Redmi / POCO (`*#*#284#*#*`)
1. Open Phone app → Dial `*#*#284#*#*`
2. Wait for bugreport to generate (2-5 min)
3. Find zip in: `/sdcard/MIUI/debug_log/`
4. Share the zip

**OR:**
1. Settings → About Phone → Tap **"MIUI version"** 7 times
2. Settings → Additional Settings → Developer Options → **"Take bug report"**

**OR CIT hardware test:**
1. Dial `*#*#64663#*#*` → Battery test

**Direct analysis:**
```bash
python3 battery_analyzer.py bugreport-*.zip --brand xiaomi
```

---

### Google Pixel / Stock Android (`*#*#284#*#*`)
1. Open Phone app → Dial `*#*#284#*#*`
2. Wait for bugreport
3. Find in: `/sdcard/bugreports/`

**OR:**
1. Settings → Developer Options → **"Take bug report"**

**Direct analysis:**
```bash
python3 battery_analyzer.py bugreport-*.zip
```

---

### Any Android (ADB — Universal Bypass)
Works on **every** Android phone. No dial codes needed.

```bash
# Enable USB debugging first:
# Settings → Developer Options → USB Debugging → ON

# Quick battery info:
adb shell dumpsys battery

# Full battery stats:
adb shell dumpsys batterystats > battery_stats.txt

# Complete bugreport (recommended):
adb bugreport > bugreport.txt

# Kernel battery data:
adb shell cat /sys/class/power_supply/battery/cycle_count
adb shell cat /sys/class/power_supply/battery/charge_full
adb shell cat /sys/class/power_supply/battery/charge_full_design
adb shell cat /sys/class/power_supply/battery/temp
adb shell cat /sys/class/power_supply/battery/voltage_now

# Then analyze:
python3 battery_analyzer.py bugreport.txt
```

**ADB battery info command (quick check):**
```bash
adb shell dumpsys battery
# Output shows: level, health, voltage, temperature, technology, etc.
```

---

### Motorola / Lenovo
1. Dial `*#*#2486#*#*` → CQA Menu → Battery
2. Or: `adb bugreport`

### Vivo / iQOO
1. Dial `*#*#556688#*#*` → Factory test
2. Or: `adb bugreport`

### Nothing Phone / CMF
1. Same as stock Android: `adb bugreport`
2. Or: `*#*#284#*#*`

---

## 🍎 Apple (iPhone / iPad)

### Method 1: Built-in (Easiest)
**iOS 11.3+ / iPadOS 13+** shows battery health directly:
1. Settings → Battery → Battery Health & Charging
2. Shows: **Maximum Capacity %** and **Peak Performance Capability**
3. Note: Apple does NOT show cycle count in the UI

**What you get:**
- Maximum Capacity % (equivalent to ASOC)
- Peak Performance Capability (throttling status)

---

### Method 2: Analytics File (Shows Cycle Count) ⭐
This is the **best method** — shows actual cycle count.

#### On iPhone:
1. Go to **Settings → Privacy & Security → Analytics & Improvements**
2. Make sure **"Share iPad Analytics"** is ON
3. Wait 24 hours (data generates daily)
4. Go to **Settings → Privacy & Security → Analytics & Improvements → Analytics Data**
5. Look for a file named: **`log-aggregated-YYYY-MM-DD-...`**
6. Open it → Tap Share → AirDrop to Mac/PC
7. Or: Copy the entire text content

#### On iPad (same process):
1. Settings → Privacy & Security → Analytics & Improvements
2. Turn ON "Share iPad Analytics"
3. Wait 24 hours
4. Settings → Privacy & Security → Analytics & Improvements → Analytics Data
5. Find `log-aggregated-*` file → Share → AirDrop

**Then extract the battery data:**
- Open the `log-aggregated` file in a text editor
- Search for `BATTERY_CYCLE_COUNT`
- Search for `BatteryCycleCount`
- The number next to it is your cycle count

**Example output:**
```xml
<key>BATTERY_CYCLE_COUNT</key>
<integer>326</integer>
```

---

### Method 3: Shortcut (Automated) ⭐⭐
The user mentioned having a shortcut — here's how it works:

1. Install the **"PowerUtil"** or **"Battery Stats"** shortcut
2. Go to Settings → Privacy & Security → Analytics & Improvements → Analytics Data
3. Open the latest `log-aggregated` file
4. Tap Share → Run the Shortcut
5. It extracts and displays: cycle count, max capacity, temperature data

**Popular shortcuts:**
- **"PowerUtil"** — extracts cycle count from analytics
- **"Battery Stats"** — parses analytics for battery info
- Search "battery shortcut" in the Shortcuts app gallery

---

### Method 4: CoconutBattery (Mac) ⭐⭐⭐
Best for detailed analysis:
1. Install **CoconutBattery** (free) on Mac: https://coconut-flavor.com/coconutbattery/
2. Connect iPhone/iPad via USB
3. CoconutBattery shows:
   - Cycle count
   - Maximum capacity (mAh)
   - Design capacity (mAh)
   - Battery health %
   - Temperature
   - Manufacturing date
   - First use date

**This is the most complete method for Apple devices.**

---

### Method 5: 3uTools (Windows) ⭐⭐⭐
1. Install **3uTools** (free): https://www.3u.com/
2. Connect iPhone/iPad via USB
3. Go to **"Device"** → **"Battery Life"**
4. Shows:
   - Charge cycles
   - Actual capacity vs design capacity
   - Battery health %
   - Temperature

---

### Method 6: sysdiagnose (Advanced)
1. Hold **Power + Home** (or Power + Volume Up on newer iPads)
2. When slider appears, hold **Power + Home** for 10 seconds
3. Device will restart and create a sysdiagnose bundle
4. Find in: Settings → Privacy & Security → Analytics → Analytics Data → `sysdiagnose-*`
5. Share to Mac/PC → Extract → Look for battery data in text files

---

## 📊 Comparison: What Each Method Gives You

| Method | Cycle Count | Health % | Capacity | Temp | Difficulty |
|--------|:-----------:|:--------:|:--------:|:----:|:----------:|
| **Samsung *#9900#** | ✅ | ✅ | ✅ | ✅ | Easy |
| **Realme *#800#** | ✅ | ✅ | ✅ | ✅ | Easy |
| **Xiaomi *#*#284#*#*** | ✅ | ✅ | ✅ | ✅ | Easy |
| **ADB bugreport** | ✅ | ✅ | ✅ | ✅ | Medium |
| **iOS Battery Health** | ❌ | ✅ | ❌ | ❌ | Easiest |
| **iOS Analytics file** | ✅ | ✅ | ❌ | ❌ | Medium |
| **CoconutBattery** | ✅ | ✅ | ✅ | ✅ | Easy |
| **3uTools** | ✅ | ✅ | ✅ | ✅ | Easy |

---

## 🔧 Our Tool Compatibility

| Platform | Parser | Status |
|----------|--------|--------|
| Samsung Android | SamsungParser | ✅ Full support |
| Realme/Oppo/OnePlus | RealmeParser | ✅ Supported |
| Xiaomi/Redmi/POCO | XiaomiParser | ✅ Supported |
| Google Pixel | GenericParser | ✅ Supported |
| Any Android (adb) | GenericParser | ✅ Supported |
| iPhone/iPad | (External tools) | ⚠️ Use CoconutBattery/3uTools |
| iPad (sysdiagnose) | (Planned) | 🔜 Coming soon |

**For Apple devices**, use CoconutBattery (Mac) or 3uTools (Windows) to get the data, then we can add an Apple parser later if needed.

---

## 📋 Quick Reference Card

```
Samsung:     *#9900# → Run dumpstate → Copy to SD
Realme:      *#800#  → Start/Stop Record → LogKit folder
OnePlus:     *#800#  → Same as Realme
Xiaomi:      *#*#284#*#*  → Bug report generated
Pixel:       *#*#284#*#*  → Bug report generated
iPhone:      Settings → Battery → Battery Health
iPad:        Settings → Battery → Battery Health
iPad (full): CoconutBattery via Mac or 3uTools via Windows
ANY PHONE:   adb bugreport > bugreport.txt
```

---

*Last updated: June 27, 2026*

---

## 🔧 Narzo 10 / Realme (Specific Process)

### What We Know
- **Model:** Realme Narzo 10 (RMX2040)
- **OS:** Realme UI (ColorOS based), Android 11
- **Build:** RMX2040_11_C.14

### How to Get Battery Health on Narzo 10

#### Method 1: Settings (Easiest)
1. Open **Settings** → **Battery**
2. Look for **"Battery Health"** or **"Battery Information"**
3. Shows: Maximum capacity % and cycle count (if available)
4. Note: Realme UI may not show cycle count in all versions

#### Method 2: Dial Code
1. Open Phone app → Dial `*#800#`
2. This opens **Logkit** (Realme's diagnostic tool)
3. Tap **"Start Record"** → Use phone for 2-3 minutes
4. Tap **"Stop Record"**
5. Find zip in: `/sdcard/LogKit/`
6. Share the zip file

**Note:** The logkit captures system logs but may NOT include detailed battery health data (ASOC, cycle count). It mainly captures:
- Battery voltage/current/temp over time
- System logs
- Network logs
- Process info

#### Method 3: ADB (Best for Full Data)
```bash
# Enable USB debugging:
# Settings → Developer Options → USB Debugging → ON

# Quick battery info:
adb shell dumpsys battery

# Full battery stats:
adb shell dumpsys batterystats > narzo10_battery.txt

# Kernel battery data:
adb shell cat /sys/class/power_supply/battery/cycle_count
adb shell cat /sys/class/power_supply/battery/charge_full
adb shell cat /sys/class/power_supply/battery/charge_full_design
adb shell cat /sys/class/power_supply/battery/temp
adb shell cat /sys/class/power_supply/battery/voltage_now

# Complete bugreport (recommended):
adb bugreport > narzo10_bugreport.txt
```

#### Method 4: Third-Party Apps
- **AccuBattery** (Play Store) — monitors battery health over time
- **Battery Guru** (Play Store) — detailed battery stats
- **CPU-Z** — shows some battery info

### Narzo 10 Battery Specs
- **Design Capacity:** 5,000 mAh
- **Charging:** 18W Quick Charge
- **Battery Type:** Li-Po (non-removable)
- **Chipset:** MediaTek Helio G80

### What the Logkit Captured
From the extracted `com.coloros.zip`:
- `dumpsys_batterystats.txt` — battery history (voltage, temp, charge level)
- `batterystats_for_bh.txt` — battery health checkin data
- `prop.txt` — system properties (model: RMX2040)
- `kernel_log` — kernel-level battery events
- `netlog/` — network activity logs

**The logkit data shows:** Battery was at 83% level, 37°C temp, 4118mV voltage at time of capture. Health status: "good".

### Recommendation for Full Battery Data
**Use ADB method** — it's the most reliable way to get cycle count and health data from the Narzo 10. The logkit is more for debugging than battery health.

---

## 🔧 Termux on Realme Narzo 10 — Complete Procedure

### Can Termux Work on Narzo 10?
**Yes!** Termux works on Realme Narzo 10 (RMX2040). It runs Android 10+ with MediaTek Helio G80, which is fully compatible.

### Step-by-Step Setup

#### 1. Install Termux
- Download from **F-Droid** (recommended) or GitHub
- **DO NOT use Play Store version** (it's outdated and broken)
- F-Droid link: https://f-droid.org/en/packages/com.termux/
- Or GitHub releases: https://github.com/termux/termux-app/releases

#### 2. Initial Setup
Open Termux and run:
```bash
# Update packages
pkg update && pkg upgrade

# Install required tools
pkg install python coreutils grep sed
```

#### 3. Get Battery Data via Termux

**Method A: Read sysfs directly (no root needed)**
```bash
# Cycle count
cat /sys/class/power_supply/battery/cycle_count

# Current capacity (mAh)
cat /sys/class/power_supply/battery/charge_full

# Design capacity (mAh)
cat /sys/class/power_supply/battery/charge_full_design

# Temperature (divide by 10 for °C)
cat /sys/class/power_supply/battery/temp

# Voltage (divide by 1000 for mV)
cat /sys/class/power_supply/battery/voltage_now

# Current (divide by 1000 for mA, negative = discharging)
cat /sys/class/power_supply/battery/current_now

# Status (Charging/Discharging/Full)
cat /sys/class/power_supply/battery/status

# Health (Good/Overheat/Dead/etc)
cat /sys/class/power_supply/battery/health

# Battery level (%)
cat /sys/class/power_supply/battery/capacity
```

**Method B: Use dumpsys (requires ADB or root)**
```bash
# If ADB over TCP is enabled:
dumpsys battery

# Or parse battery info:
dumpsys batterystats | head -50
```

**Method C: Quick one-liner**
```bash
# All battery info at once:
echo "=== Battery Info ===" && \
echo "Cycles: $(cat /sys/class/power_supply/battery/cycle_count 2>/dev/null || echo 'N/A')" && \
echo "Capacity: $(cat /sys/class/power_supply/battery/charge_full 2>/dev/null || echo 'N/A') mAh" && \
echo "Design: $(cat /sys/class/power_supply/battery/charge_full_design 2>/dev/null || echo 'N/A') mAh" && \
echo "Temp: $(($(cat /sys/class/power_supply/battery/temp 2>/dev/null || echo 0) / 10))°C" && \
echo "Voltage: $(($(cat /sys/class/power_supply/battery/voltage_now 2>/dev/null || echo 0) / 1000)) mV" && \
echo "Level: $(cat /sys/class/power_supply/battery/capacity 2>/dev/null || echo 'N/A')%" && \
echo "Status: $(cat /sys/class/power_supply/battery/status 2>/dev/null || echo 'N/A')"
```

#### 4. Copy Data to PC
```bash
# Option 1: Save to file and share via Telegram
battery_info.txt
cat /sys/class/power_supply/battery/* > battery_dump.txt
# Then share battery_dump.txt via Telegram

# Option 2: Use Termux:API for clipboard
pkg install termux-api
cat /sys/class/power_supply/battery/cycle_count | termux-clipboard-set
# Then paste on PC

# Option 3: Use termux-file-editor
# Share files directly from Termux
```

#### 5. Analyze with Our Tool
```bash
# On your Mac, after getting the file:
python3 battery_analyzer.py battery_dump.txt --brand realme
```

### Narzo 10 Specific sysfs Paths
```
/sys/class/power_supply/battery/cycle_count      → Cycle count
/sys/class/power_supply/battery/charge_full       → Current full capacity (mAh)
/sys/class/power_supply/battery/charge_full_design → Design capacity (mAh)
/sys/class/power_supply/battery/temp              → Temperature (÷10 = °C)
/sys/class/power_supply/battery/voltage_now       → Voltage (÷1000 = mV)
/sys/class/power_supply/battery/current_now       → Current (÷1000 = mA)
/sys/class/power_supply/battery/status            → Charging/Discharging/Full
/sys/class/power_supply/battery/health            → Good/Overheat/Dead
/sys/class/power_supply/battery/capacity          → Level (%)
/sys/class/power_supply/battery/technology        → Li-ion/Li-poly
```

### Important Notes for Narzo 10
- **No root needed** for sysfs reads
- **Termux from F-Droid only** — Play Store version is broken
- **Some paths may differ** on ColorOS/Realme UI — if one path doesn't work, try alternatives
- **If cycle_count shows N/A**, the kernel may not expose it — use `adb shell dumpsys battery` instead

---

### iQOO / Vivo
1. Dial `*#*#556688#*#*` → Factory Test → Battery
2. Or: `adb bugreport`
3. Or: Settings → Battery → Battery Health

**Direct analysis:**
```bash
python3 battery_analyzer.py bugreport.txt --brand vivo
```
