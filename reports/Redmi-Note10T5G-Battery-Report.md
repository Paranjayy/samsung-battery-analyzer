# 🔋 Xiaomi Redmi Note 10T 5G Battery Report

> **Date:** August 7, 2026 | **Source:** Redmi Diagnostics (*#*#284#*#*)

---

## 📱 Device Info

| Field | Value |
|-------|-------|
| Model | Xiaomi Redmi Note 10T 5G (M2103K19I) |
| Codename | camellia_in |
| Android | 13 (SDK 33) |
| MIUI | 14 (V14.0.6.0.TKSINXM) |
| Security Patch | September 1, 2023 |
| Kernel | Linux 4.14.186-perf (MediaTek) |
| Display | 1080x2400, 60Hz |
| RAM | 3.5 GB |
| Storage | 49 GB (28 GB free) |
| Bootloader | Locked |
| Verified Boot | Green (Verified) |
| Uptime | 36 minutes (since last boot) |

---

## 📊 Battery Health Summary

| Metric | Value | Rating |
|--------|-------|--------|
| **Battery Level** | **71%** | - |
| **Status** | Charging (USB) | 🐌 Slow |
| **Health** | **Good** | 🟢 Healthy |
| **Technology** | Li-poly | - |
| **Temperature** | 38.0°C | 🟡 Slightly Warm |
| **Voltage** | 4,013 mV | 🟢 Normal |
| **Charge Counter** | 2,024 mAh | - |
| **Max Charging Current** | 500 mA | 🐌 USB 2.0 |
| **Max Charging Voltage** | 5,000 mV (5V) | - |

---

## 🔍 What the Numbers Mean

### Health: Good
The battery health status reports as **"Good"** — no degradation warnings, no overheat flags. This is a healthy battery.

### Temperature: 38.0°C
Slightly warm but within normal range. The phone was likely in use or charging when captured. No thermal concerns.

### Voltage: 4,013 mV
Healthy voltage level. Li-poly batteries operate between 3.0V (empty) and 4.2V (full). At 4.013V, the battery is in its optimal discharge range.

### Charging: USB Only (500mA)
The phone is charging via USB at only 500mA — this is USB 2.0 standard speed. Very slow. The Redmi Note 10T 5G supports **18W fast charging** (22.5W charger included in box) but requires a compatible charger and cable.

---

## 📈 Battery History Analysis (Last 2 Hours)

### Discharge Pattern

| Time | Level | Voltage | Temp | Notes |
|------|-------|---------|------|-------|
| 0:00 | 94% | 4,222 mV | 30.4°C | Reset, discharging |
| +4 min | 93% | 4,204 mV | - | First drop |
| +29 min | 92% | 4,193 mV | 31.7°C | Steady discharge |
| +41 min | 90% | 4,114 mV | - | Accelerating |
| +52 min | 89% | 4,048 mV | 37.6°C | Temp rising |
| +1h 20m | 80% | - | - | Rapid drain |
| +1h 50m | 73% | - | - | Heavy usage |
| +2h 05m | 71% | 4,013 mV | 38.0°C | Capture time |

### Key Observations

1. **23% drain in ~2 hours** — approximately 11.5% per hour
2. **Temperature rose from 30.4°C to 38.0°C** — 7.6°C increase during usage
3. **Voltage dropped from 4,222 mV to 4,013 mV** — 209 mV drop
4. **Screen was on for most of the period** — brightness changed multiple times

---

## 🔋 Battery Drain Breakdown

### Wake Lock Activity (Major Battery Drainers)

| Wake Lock | Owner | Frequency | Impact |
|-----------|-------|-----------|--------|
| WiFi | System | Constant | 🟡 Medium |
| Bluetooth | System | Frequent | 🟡 Medium |
| Location | Google Play Services | Frequent | 🟠 High |
| Telephony | Phone/Radio | Periodic | 🟢 Low |
| Audio | Media apps | Occasional | 🟢 Low |
| Sensors | Various | Frequent | 🟡 Medium |

### App Activity During Capture

| App | Status | Notes |
|-----|--------|-------|
| com.miui.securitycenter | Foreground | MIUI Security |
| com.miui.misound | Foreground | MIUI Sound |
| com.happymod.apk | Foreground | HappyMod (modded apps) |
| com.google.android.permissioncontroller | Top | Permission management |
| com.spotify.music | Background | Music streaming |
| com.facebook.katana | Background | Facebook |
| com.google.android.youtube | Background | YouTube |

---

## 🌡️ Thermal Analysis

### Current Temperatures

| Component | Temperature | Status |
|-----------|-------------|--------|
| CPU | 45.6°C | 🟡 Warm |
| GPU | 45.6°C | 🟡 Warm |
| NPU | 45.6°C | 🟡 Warm |
| Battery | 38.0°C | 🟢 Normal |
| Skin | 40.2°C | 🟡 Warm |
| Power Amplifier | 38.6°C | 🟢 Normal |

### Peak Temperatures (Since Boot)

| Component | Peak | Status |
|-----------|------|--------|
| CPU | 57.5°C | 🟠 Hot |
| GPU | 57.5°C | 🟠 Hot |
| NPU | 57.5°C | 🟠 Hot |
| Skin | 41.2°C | 🟡 Warm |

### Thermal Status: **Normal**
No thermal throttling active. The CPU/GPU hit 57.5°C during initial boot-up (normal for MediaTek Dimensity 700), but settled down to 45.6°C during regular use.

---

## 💾 Memory & Storage

### RAM Usage

| Metric | Value | Status |
|--------|-------|--------|
| Total RAM | 3,692 MB | 3.5 GB |
| Free RAM | 281 MB | 🟡 Low |
| Available RAM | 1,093 MB | 🟢 Adequate |
| Cached | 1,012 MB | 🟢 Good |
| Swap Total | 4,194 MB | 4 GB |
| Swap Free | 1,742 MB | 🟢 Healthy |

### Storage

| Partition | Total | Used | Available | Usage |
|-----------|-------|------|-----------|-------|
| /data | 49 GB | 21 GB | 28 GB | 43% 🟢 |
| /system | 1.3 GB | 1.3 GB | 0 MB | 100% 🔒 |
| /vendor | 1.1 GB | 1.1 GB | 0 MB | 100% 🔒 |
| /product | 4.4 GB | 4.4 GB | 0 MB | 100% 🔒 |

---

## 📊 Charging Analysis

### Current Charging State

| Metric | Value |
|--------|-------|
| Source | USB (not AC) |
| Max Current | 500 mA |
| Max Voltage | 5,000 mV (5V) |
| Power | 2.5W |

### Charging Speed Comparison

| Charger Type | Current | Power | Time to Full (estimated) |
|--------------|---------|-------|--------------------------|
| **USB 2.0 (current)** | 500 mA | 2.5W | ~4-5 hours |
| USB 3.0 | 900 mA | 4.5W | ~3 hours |
| **18W Fast (max supported)** | 2,000 mA | 18W | ~1.5 hours |
| 22.5W (in-box charger) | 2,250 mA | 22.5W | ~1.2 hours |

**Recommendation:** Use the original 67W charger or a QC 3.0+ compatible charger for fast charging. USB charging at 500mA is extremely slow.

---

## 🔮 Predictions & Insights

### Estimated Usage Pattern

| Metric | Estimate |
|--------|----------|
| Battery drain rate | ~11.5% per hour (with screen on) |
| Estimated screen-on time | ~6-7 hours |
| Estimated standby time | ~48-72 hours |
| Daily charge cycles | ~1-1.5 cycles |

### Battery Age Analysis

| Metric | Value |
|--------|-------|
| Security Patch | September 2023 |
| Firmware Build | 2023 |
| Estimated Purchase | Late 2023 / Early 2024 |
| Estimated Age | ~2-3 years |
| Health Status | Good |
| Launch Date | July 2021 |

---

## 🧠 Interesting Findings

1. **MediaTek Dimensity 700** — 5G-capable mid-range chipset, 7nm architecture
2. **18W fast charging supported** (22.5W in-box) — but only 500mA USB charging captured
3. **MIUI 14** — latest MIUI version for this device
4. **3.5 GB RAM** — modest for 2026, but sufficient for light usage
5. **HappyMod installed** — modded app store, potential security risk
6. **Bluetooth active** — likely connected to accessories
7. **WiFi excellent (4/4)** — strong signal, good for battery
8. **Phone signal great** — good cellular reception
9. **5G capable** — first 5G phone from Redmi Note series
10. **5000mAh battery** — large capacity for all-day usage

---

## 💡 Recommendations

### Immediate Actions

1. **Use proper charger** — the 18W fast charger (22.5W in-box) will charge 7x faster than USB
2. **Check HappyMod** — modded apps can drain battery and pose security risks
3. **Monitor background apps** — Facebook and YouTube running in background

### Battery Health

1. **Battery is healthy** — "Good" status with normal temperature
2. **No replacement needed** — continue normal usage
3. **Avoid extreme temps** — 57.5°C peak is fine, but try to stay below 45°C

### Performance

1. **RAM is adequate** — 1GB free is enough for light tasks
2. **Storage is healthy** — 57% free on data partition
3. **Consider closing background apps** — Facebook, YouTube, Spotify running

### Long-term

1. **Track battery health** — install AccuBattery to monitor over time
2. **Avoid overnight charging** — helps preserve long-term health
3. **Keep software updated** — MIUI updates often include battery optimizations

---

## 🔬 Raw Data

```
=== Battery Service State ===
AC powered: false
USB powered: true
Wireless powered: false
Max charging current: 500000
Max charging voltage: 5000000
Charge counter: 2024210
status: 2 (Charging)
health: 2 (Good)
present: true
level: 71
scale: 100
voltage: 4013
temperature: 380 (38.0°C)
technology: Li-poly

=== Device Info ===
Model: M2103K19I
Device: camellia
Product: camellia_in
Android: 13
SDK: 33
Security patch: 2023-09-01
Build: V14.0.6.0.TKSINXM
Kernel: 4.14.186-perf-gf8d872e9279c

=== Thermal ===
CPU: 45.6°C (peak: 57.5°C)
GPU: 45.6°C (peak: 57.5°C)
Battery: 38.0°C
Skin: 40.2°C (peak: 41.2°C)
NPU: 45.6°C (peak: 57.5°C)
Power Amplifier: 38.6°C

=== Memory ===
MemTotal: 3692576 kB
MemFree: 281040 kB
MemAvailable: 1093196 kB
SwapTotal: 4194300 kB
SwapFree: 1742268 kB
```

---

*Report generated by Universal Battery Analyzer*
*Source: Redmi_Diagnostics_2026-08-07_04-03-03.zip*
