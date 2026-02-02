# Advanced Trading Analytics Metrics

## 📊 Available Metrics

### Core Performance Metrics

| Metric | Description | Formula | Interpretation |
|--------|-------------|---------|-----------------|
| **Total PnL** | Overall profit/loss | Sum of all trade PnL | Positive = Profitable |
| **Win Rate** | Percentage of winning trades | (Wins / Total) × 100 | 50%+ is acceptable, 60%+ is good |
| **Profit Factor** | Ratio of gross profit to loss | Total Profit / Total Loss | >1.5 is excellent, >1.0 is acceptable |
| **Avg Win/Loss** | Average profit on winners/losers | Total Profit(Loss) / Count | Identifies trade quality |
| **Expectancy** | Expected value per trade | (WR × AvgW) - ((1-WR) × AvgL) | Positive = edge |
| **Risk-Reward Ratio** | Win size vs loss size | Avg Win / Avg Loss | 1:2+ is ideal |

### Risk Metrics

| Metric | Description | Interpretation |
|--------|-------------|-----------------|
| **Max Drawdown** | Largest peak-to-trough decline | Measures worst case scenario |
| **Avg Drawdown** | Average decline from peak | Overall risk exposure |
| **Sharpe Ratio** | Risk-adjusted returns | >1 = good, >2 = excellent |
| **Standard Deviation** | Volatility of returns | Lower = more consistent |
| **Kelly Criterion** | Optimal position sizing | f = (WR × RR - (1-WR)) / RR |

### Consistency Metrics

| Metric | Description | Interpretation |
|--------|-------------|-----------------|
| **Max Consecutive Wins** | Best winning streak | Shows momentum capability |
| **Max Consecutive Losses** | Worst losing streak | Defines risk tolerance |
| **Trades/Day** | Average trading frequency | Activity level |
| **Trading Days** | Days with trades | Sample size validation |
| **Avg Trade Duration** | Average hold time | Trade timing |

### Breakdown Metrics

| Category | Metrics Tracked |
|----------|-----------------|
| **By Option Type** | CE vs PE - Count, PnL, Win Rate |
| **By Index** | NIFTY, BANKNIFTY, FINNIFTY - Individual performance |
| **By Exit Reason** | SL Hit, Target, Reversal - Strategy effectiveness |
| **By Time Period** | Daily stats - Seasonal patterns |

---

## 🎯 Interpretation Guide

### Healthy Trading Strategy Profile
```
✓ Win Rate: 45-65%
✓ Profit Factor: 1.5-3.0
✓ Risk-Reward: 1:2 or better
✓ Max Drawdown: <25% of total PnL
✓ Sharpe Ratio: >1
✓ Consecutive Losses: <5
✓ Consistent daily trading
```

### Warning Signs
```
⚠ Win Rate < 40% (need better entry/exit)
⚠ Profit Factor < 1.0 (losing money)
⚠ Max Drawdown > 50% of PnL (excessive risk)
⚠ Consecutive Losses > 10 (strategy breakdown)
⚠ High std deviation (inconsistent results)
⚠ Sharpe Ratio < 0.5 (poor risk-adjusted returns)
```

---

## 📈 Using the Analytics

### 1. Daily Performance Review
1. Open "Trade Analysis" → "Overview" tab
2. Check "Advanced Metrics" section
3. Look for "Trading Days" and "Avg Trades/Day"
4. Verify daily PnL is positive

### 2. Strategy Assessment
1. Compare "Win Rate" to "Profit Factor"
2. Calculate Risk-Reward: Avg Win ÷ Avg Loss
3. Check "Max Consecutive Losses"
4. Review exit reasons for pattern

### 3. Risk Management Check
1. Monitor "Max Drawdown" trend
2. Ensure "Sharpe Ratio" > 1
3. Validate "Max Consecutive Losses" < threshold
4. Check daily loss limits are respected

### 4. Improvement Areas
1. Low Win Rate? → Focus on entry signal quality
2. Low Profit Factor? → Improve exit strategy
3. High Drawdown? → Reduce position size or add filters
4. Inconsistent profits? → Add entry/exit criteria

---

## 💡 Advanced Insights

### Expectancy Calculation
```python
Expectancy = (Win_Rate × Avg_Win) - (Loss_Rate × Avg_Loss)

Example:
- Win Rate: 55% | Avg Win: ₹100
- Loss Rate: 45% | Avg Loss: ₹80
- Expectancy = (0.55 × 100) - (0.45 × 80) = 55 - 36 = ₹19/trade
```
✓ Positive expectancy = Strategy has edge

### Kelly Criterion (Position Sizing)
```python
f = (2p - 1) / b
where: p = win% | b = loss/win ratio

Example:
- 60% win rate | 1:1.5 reward:risk
- f = (2×0.6 - 1) / (1.5/1) = 0.2 / 1.5 = 13.3%
```
✓ Optimal position size = 13.3% per trade

### Sharpe Ratio
```python
Sharpe = (Avg_Return - Risk_Free_Rate) / Std_Dev

Example:
- Avg daily PnL: ₹500
- Std Dev: ₹1000
- Risk-free: 5% annual ≈ 0.014% daily
- Sharpe ≈ (500 - 0.14) / 1000 = 0.5
```
✓ >1 = Good, >2 = Excellent

---

## 📊 Filter & Analysis Options

### Available Filters
- ✓ Date Range (Today, Week, Month, Custom)
- ✓ Option Type (CE, PE, All)
- ✓ Index (NIFTY, BANKNIFTY, FINNIFTY, SENSEX)
- ✓ Exit Reason (Target, SL, Reversal)
- ✓ Mode (Paper, Live)
- ✓ Strike Range (Custom filter)
- ✓ PnL Range (Min/Max filter)

### Common Analysis Scenarios

#### Scenario 1: "Why is my win rate low?"
1. Filter by exit reason
2. Compare "Target" vs "SL Hit" ratios
3. Adjust entry signals for better entries
4. OR widen stop loss tolerance

#### Scenario 2: "Trading is too volatile"
1. Check Standard Deviation in metrics
2. Reduce position size (lower %)
3. Add entry filters (confluence)
4. Increase trailing stop margin

#### Scenario 3: "Too many consecutive losses"
1. Check "Max Consecutive Losses" metric
2. Analyze daily stats for pattern
3. Add market condition filters
4. Increase daily loss limits temporarily

---

## 🔄 Continuous Improvement Cycle

```
1. Review Analytics
   ↓
2. Identify Weak Area
   ↓
3. Test Hypothesis
   ↓
4. Paper Trade Change
   ↓
5. Measure Results (via Analytics)
   ↓
6. Accept or Reject Change
   ↓
7. Repeat
```

---

## 📱 Mobile View

All metrics are responsive and mobile-friendly. View analytics on:
- Desktop: Full grid layout
- Tablet: 2-column layout
- Mobile: Stacked single column

---

## 🔗 Related Pages

- **Dashboard** - Real-time trading status
- **Trade Analysis** - Detailed trade history & filters
- **Settings** - Configure trading parameters
- **Logs Viewer** - Debug order execution

