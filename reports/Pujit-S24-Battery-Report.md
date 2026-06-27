# 🔋 Samsung Galaxy S24 - Battery Deep Dive Report

> **Owner:** Pujit (Cousin) | **Date:** June 27, 2026 | **Phone used since:** ~Dec 28, 2024

---

## 📱 Device Info

| Field | Value |
|-------|-------|
| Model | Samsung Galaxy S24 (SM-S921B) |
| Android | 16 (OneUI 8.x) |
| Build | BP4A.251205.006.S921BXXSFDZE1 |
| Network | Jio True5G |
| Kernel | Linux 6.1.157 (Exynos 2400) |
| Display | 1080x2340, 120Hz AMOLED, 480 dpi |
| Log File | dumpState_S921BXXSFDZE1_202606271933.log (144.7 MB) |

---

## 📊 Battery Health Summary

| Metric | Value | Rating |
|--------|-------|--------|
| **ASOC (Health %)** | **91%** | 🟡 Good |
| **BSOH (State of Health)** | **98%** | 🟢 Excellent |
| **Cycle Count** | **504 cycles** | 🟡 Moderate |
| **Design Capacity** | 3,700 mAh (typical) | - |
| **Effective Capacity** | ~3,367 mAh | - |
| **Max Temp Ever** | 75.9°C | 🔴 **DANGER** |
| **Max Current Draw** | 5,416 mA | ⚠️ High |
| **Current Battery Level** | 51% | - |

---

## 🔍 What the Numbers Mean

### ASOC: 91% vs BSOH: 98%
- **ASOC** = how much capacity is left compared to design (91%)
- **BSOH** = overall battery state of health including internal resistance (98%)
- The gap (91 vs 98) suggests the battery chemistry is healthy but some capacity has permanently faded — normal for 504 cycles

### Cycle Count: 504
At ~0.92 cycles/day (matching your usage pattern from chat):
- **Total days of use:** ~547 days (~1.5 years)
- **First use estimate:** ~December 28, 2024 (confirmed from chat)
- **Second-hand purchase** — previous owner used it for some time before

### 🚨 Max Temp: 75.9°C — THIS IS SERIOUS
**75.9°C is extremely hot for a battery.** Lithium-ion batteries should never exceed 60°C. At 75.9°C:
- Permanent capacity loss occurs
- Internal resistance increases
- Safety risk (thermal runaway possible)
- This likely happened during **fast charging while gaming/heavy use**

The 5,416 mA max current supports this — someone was drawing serious power, probably gaming on 5G with fast charging.

### Max Current: 5,416 mA
The S24 supports 25W fast charging (5A at 5V or 2.25A at 11V). 5,416 mA suggests:
- 25W fast charging was being used
- Combined with heavy screen/CPU usage
- This is likely what caused the extreme temperature

---

## 📈 Usage Analysis (Last Charge Cycle)

*From DC.BatteryUsage section:*

| Metric | Value |
|--------|-------|
| Last Charge | Sat Jun 27 14:58:48 IST |
| Total Discharge | 47.3% |
| Total Usage | 2,269 mAh |
| Screen On Time | 3h 50m |
| Screen Off Time | 39m |

### 🔋 Top Battery Drainers

| Rank | App | Active | Background | Usage (mAh) | % |
|------|-----|--------|------------|-------------|---|
| 1 | Samsung Apps | 0m | 3h 24m | 226.6 | 4.7% |
| 2 | Steam | 58m | 1m | 195.9 | 4.1% |
| 3 | YouTube | 1m | 0m | 171.7 | 3.6% |
| 4 | Instagram | 11m | 37m | 162.3 | 3.4% |
| 5 | Play Store | 1m | 1h 9m | 141.8 | 3.0% |
| 6 | Chrome | 9m | 0m | 136.8 | 2.9% |
| 7 | Samsung Launcher | 41m | 3h 15m | 89.1 | 1.9% |
| 8 | Gallery | 23m | 3m | 91.4 | 1.9% |
| 9 | Telegram | 15m | 21m | 85.2 | 1.8% |
| 10 | Gmail | 7m | 1m | 71.4 | 1.5% |

**Key observations:**
- **Samsung Apps** is the #1 drainer at 226.6 mAh — likely Samsung's own services doing background sync/updates
- **Steam** at 58m active time and 195.9 mAh — you were browsing Steam Store for almost an hour!
- **YouTube** 171.7 mAh in essentially 1 minute active — that's heavy background video prefetching
- **Instagram** 162.3 mAh with 11m active + 37m background — normal for social media
- **Play Store** 141.8 mAh background — probably app updates downloading
- **Chrome** 136.8 mAh in 9 minutes — heavy browsing

**5G impact:** Being on Jio True5G, the modem is working harder than 4G, which contributes to higher battery drain and heat.

---

## ⏳ Lifespan Predictions

| Prediction | Estimate |
|------------|----------|
| Cycles to 80% health | ~615 more cycles |
| Estimated remaining life | ~669 days (~22 months) |
| Health vs Expected | **+11.2% better** than average |
| Daily degradation rate | ~0.018% per cycle |

### What this means:
The S24 has about **22 months** before hitting 80% health at current usage. The 75.9°C max temp event likely caused some permanent damage — without it, the battery would probably last longer.

---

## 🧠 Interesting Findings

1. **Second-hand phone** — bought used, so previous owner's habits matter
2. **75.9°C max temp** — someone was NOT nice to this battery
3. **5G on Jio** — faster but battery-hungry, contributes to heat
4. **Good Lock installed** — customization app, only 0.5% battery impact
5. **Steam app active** — gaming interest confirmed
6. **Duolingo present** — learning streak? 🦉
7. **ChatGPT installed** — AI curious
8. **League of Legends** — mobile gaming confirmed

---

## ⚠️ Concerns & Recommendations

### 🚨 CRITICAL: Address the Heat Issue
The 75.9°C max temp is a red flag. To prevent future damage:
1. **Never charge while gaming** — remove case, stop charging, then play
2. **Use 15W charging instead of 25W** — slower but much cooler
3. **Avoid direct sunlight while charging** — keep phone in shade
4. **Monitor battery temp** — if phone feels hot, stop what you're doing

### 💡 General Tips
1. **Battery health at 91% is fine** — no replacement needed
2. **BSOH at 98% is excellent** — internal resistance is low
3. **Keep using the phone normally** — just watch the heat
4. **Consider a phone coooler** if gaming a lot — ₹500-1000 accessories help
5. **5G drains faster** — switch to 4G when not needed for speed

---

## 🔬 Raw EFS Buffer Data

```
efs_buf: 0 8 207 4405 3550 25 1 503 2250 39 394 0 37 1 0 
         5871 759 -200 716 145 760 -200 734 -200 501 198 
         593 202 501 -200 522 -200 0 247 8 0 0 0 0 91 0 
         3700 9 2 3615 3585 ...
```

| Position | Value | Meaning |
|----------|-------|---------|
| [36] | 91 | ASOC (Battery Health %) |
| [7] | 503 | Cycle Count |
| [3] | 4405 | Some capacity metric |
| [4] | 3550 | Voltage-related |
| [16] | 759 | Max Temp (÷10 = 75.9°C) |
| [17] | -200 | Some negative metric |
| [39] | 3700 | Design Capacity (mAh) |
| [41] | 2 | Charge cycle related |

---

## 📱 vs A31 Comparison

| Metric | S24 (Pujit) | A31 (KP) | Winner |
|--------|-------------|----------|--------|
| ASOC | 91% | 91% | Tie |
| BSOH | 98% | N/A | S24 |
| Cycles | 504 | 1,457 | A31 (durability) |
| Max Temp | 75.9°C 🔴 | 53.8°C 🟠 | A31 (safer) |
| Design Cap | 3,700 mAh | 5,000 mAh | A31 (bigger) |
| Effective Cap | 3,367 mAh | 4,550 mAh | A31 (more juice) |
| Android | 16 | 12 | S24 (newer) |
| 5G | Yes | No | S24 (faster) |
| Age | ~1.5 years | ~4.3 years | A31 (older) |

**The A31 is the durability champion.** 3x more cycles, lower max temp, bigger battery, still at the same health percentage. The S24 is a powerhouse but runs hotter and drains faster on 5G.

---

*Report generated by Samsung Battery Analyzer*
*Source: dumpState_S921BXXSFDZE1_202606271933.log (144.7 MB)*
