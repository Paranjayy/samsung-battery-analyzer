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
