# Trading Bot - Exact Entry & Exit Conditions

## ENTRY CONDITIONS

### When Entry is ALLOWED:
1. **Market Status Check**
   - ✅ Market must be OPEN (9:25 AM - 3:10 PM IST)
   - ✅ Must be a WEEKDAY (Mon-Fri)
   - ✅ Before 3:10 PM IST (entry cutoff)

2. **SuperTrend Signal**
   - ✅ Wait for SuperTrend to generate signal on candle close
   - ✅ GREEN signal → Buy CE (Call)
   - ✅ RED signal → Buy PE (Put)

3. **Strike Selection**
   - Current Index LTP → Find ATM (At The Money) strike
   - Round to nearest strike interval (NIFTY: 50 pts, BANKNIFTY: 100 pts)

4. **Entry Price**
   - Get real LTP from Dhan API (or simulated in PAPER mode)
   - Round to nearest 0.05 (tick size)

### When Entry is BLOCKED:
- ❌ No position currently open (can't double trade)
- ❌ Market is CLOSED
- ❌ Before 9:25 AM IST or after 3:10 PM IST
- ❌ Less than 1 candle since last exit (minimum 1 candle gap)

---

## EXIT CONDITIONS

### Exit Happens When ANY of These Occur:

#### 1. **SuperTrend Reversal (Candle Close)**
```
Holding CE (Call) → SuperTrend flips RED → EXIT
Holding PE (Put)  → SuperTrend flips GREEN → EXIT
```
- Checked on every candle close
- Most common exit

#### 2. **Initial Stop Loss (On Every Tick)**
```
Entry Price - Initial SL points = SL Level
If Option LTP <= SL Level → EXIT
```
- Default: 50 points below entry
- Checked on EVERY TICK (responsive)
- Can be disabled (0 = off)

#### 3. **Max Loss Per Trade (On Every Tick)**
```
If Loss Amount >= Max Loss Limit → EXIT
Example: Max Loss = ₹500
```
- Only if enabled (default: 0 = disabled)
- Can be disabled

#### 4. **Target Hit (On Every Tick)**
```
If Profit >= Target Points → EXIT
Example: Target = 100 points
```
- Only if enabled (default: 0 = disabled)

#### 5. **Trailing Stop Loss (On Every Tick)**
```
1. Wait for trade to profit >= Trail Start Profit (e.g., 10 pts)
2. Set trailing SL at: (Current LTP - Trail Step)
3. If LTP drops below trailing SL → EXIT

Example:
- Entry: 100, Trail Start: 10, Trail Step: 5
- Profit reaches 15 pts → Trailing SL = 110
- If LTP drops to 109 → EXIT with 9 pts profit
```
- Only if both Trail Start > 0 AND Trail Step > 0
- Default: Trail Start = 0, Trail Step = 0 (DISABLED)

#### 6. **Force Square Off at 3:25 PM IST**
```
At 3:25 PM IST → Force exit ALL open positions
This ensures no overnight positions
```

---

## CURRENT CONFIGURATION

### Default Settings:
```
Initial SL: 50 pts          ✅ ACTIVE
Max Loss Per Trade: ₹0      ❌ DISABLED
Target Points: 0 pts        ❌ DISABLED
Trail Start Profit: 0 pts   ❌ DISABLED
Trail Step: 0 pts           ❌ DISABLED
```

### Exit Priority (in order):
1. SuperTrend Reversal (FIRST - main exit)
2. Initial SL (always active if entry made)
3. Force Square Off at 3:25 PM (end of day)
4. Daily Max Loss (stops all trading for the day)
5. Max Trades/Day (stops if limit reached)

---

## POSITION SIZING

### Default:
```
order_qty = 1 lot
NIFTY lot_size = 50
Total Qty = 1 × 50 = 50 contracts
```

### Dynamic Sizing (if Risk Per Trade enabled):
```
Position Size = Risk Amount / (SL Points × Lot Size)
Example:
- Risk ₹500, SL 50 pts, Lot Size 50
- Size = 500 / (50 × 50) = 0.2 lots ≈ 1 lot
```

---

## TIME CONSTRAINTS

### Allowed to TAKE NEW TRADES:
- ✅ 9:25 AM IST - 3:10 PM IST (Mon-Fri only)

### Must EXIT ALL TRADES BY:
- 🔴 3:25 PM IST (Force square off)
- 🔴 3:30 PM IST (Market close)

### Candle Interval:
- Default: 5 seconds
- Each candle analyzed on close

---

## RISK MANAGEMENT

### Daily Loss Limits:
```
If Daily PnL < -Daily Max Loss → STOP TRADING
Example: Daily Max Loss = ₹2000
If loss reaches ₹2000 → No more trades until tomorrow
```

### Max Trades Per Day:
```
If trades taken >= Max Trades Per Day → STOP TAKING NEW ENTRIES
Example: Max Trades = 5
After 5 trades → No new entries (existing can exit)
```

### Per-Trade Max Loss:
```
If single trade loss >= Max Loss Per Trade → EXIT
Example: Max Loss Per Trade = ₹500
Disabled by default (0)
```

---

## ENTRY LOGIC FLOW

```
Start
  ↓
[Check] Market Open? → NO → WAIT
  ↓ YES
[Check] Within Trading Hours (9:25-3:10)? → NO → WAIT
  ↓ YES
[Check] Already have position? → YES → SKIP
  ↓ NO
[Check] Candle Complete? → NO → WAIT
  ↓ YES
[Check] SuperTrend Generated Signal? → NO → WAIT
  ↓ YES (GREEN or RED)
[Check] Time since last exit >= 1 candle? → NO → WAIT
  ↓ YES
[GET] ATM Strike
[GET] Entry Price (Dhan API or Simulated)
[PLACE] BUY order for CE (if GREEN) or PE (if RED)
  ↓
POSITION OPEN ✓
```

---

## EXIT LOGIC FLOW (Checked Every Tick & Every Candle)

```
Every Tick (1 second):
  ↓
[Check] Do we have open position? → NO → CONTINUE
  ↓ YES
[Check] Option LTP <= Initial SL? → YES → EXIT (SL Hit)
  ↓ NO
[Check] Loss > Max Loss Per Trade? → YES → EXIT (Max Loss)
  ↓ NO
[Check] Profit >= Target? → YES → EXIT (Target)
  ↓ NO
[Check] Profit >= Trail Start AND LTP <= Trailing SL? → YES → EXIT (Trail SL)
  ↓ NO
CONTINUE

Every Candle Close:
  ↓
[Check] SuperTrend reversed? (GREEN→RED or RED→GREEN) → YES → EXIT (ST Reversal)
  ↓ NO
CONTINUE

At 3:25 PM IST:
  ↓
FORCE EXIT ALL POSITIONS
```

---

## EXAMPLE SCENARIOS

### Scenario 1: Normal Entry & SuperTrend Exit
```
9:15 AM - Market Opens
9:45 AM - Candle closes with GREEN signal
        → Enter CE at 100
        → Set SL at 50 (100-50)

10:15 AM - Price goes to 110 (profit +10)
10:30 AM - Price drops to 95 (loss -5)
          → SL not hit yet (still above 50)

11:00 AM - Candle closes with RED signal
        → SuperTrend reversed
        → EXIT at market price (~95)
        → Result: -5 points loss
```

### Scenario 2: Quick SL Hit
```
2:00 PM - Enter PE at 50
2:01 PM - Price drops to 49.5
         → Check SL: Entry(50) - SL(50) = 0
         
2:02 PM - Price drops to 0 (touches SL)
       → EXIT immediately
       → Result: -50 points loss (SL hit)
```

### Scenario 3: Target Hit
```
2:15 PM - Enter CE at 100 with Target = 100 pts
2:20 PM - Price goes to 200
        → Check: Profit (100) >= Target (100)
        → EXIT at 200
        → Result: +100 points profit ✓
```

### Scenario 4: Force Exit at EOD
```
3:00 PM - Have open CE position at 110
3:25 PM - Approaching force square off time
       → Position force exited at current market price
       → Result: Whatever price was at 3:25 PM
```

---

## SUMMARY

**ENTRY:**
- Wait for GREEN/RED signal from SuperTrend on candle close
- Market must be open, before 3:20 PM
- Position must be closed (no doubling)

**EXIT:**
- SuperTrend reversal (PRIMARY)
- Initial SL 50 pts (ALWAYS ACTIVE)
- Target (if enabled)
- Trailing SL (if enabled)
- Max loss per trade (if enabled)
- Force at 3:25 PM (ALWAYS)

**SAFETY:**
- Daily max loss limit ✓
- Per trade SL ✓
- Max trades/day ✓
- Market hours check ✓

---

**Status**: Production Ready ✅
**Last Updated**: January 29, 2026
