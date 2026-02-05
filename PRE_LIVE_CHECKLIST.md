# 🚨 PRE-LIVE CHECKLIST - DO THIS BEFORE GOING LIVE TOMORROW

## ⚠️ CRITICAL CHECKS

### 1. **Market Status Verification** (MUST DO)
```
BEFORE starting live trading:

1. Open Dashboard
2. Look at Top Bar - check "🔴 CLOSED" or "🟢 OPEN"
3. It should show ACTUAL IST time
4. If it says OPEN when market is CLOSED = DO NOT TRADE

Example of CORRECT display:
- 9:15 AM IST → Shows "🟢 OPEN"
- 3:31 PM IST → Shows "🔴 CLOSED"
- Sunday → Shows "🔴 CLOSED"
- Saturday → Shows "🔴 CLOSED"
```

### 2. **Verify Market Hours**
```
NSE India Market Hours:
- Opens: 9:15 AM IST
- Closes: 3:30 PM IST
- Trading Allowed: Mon-Fri (Weekdays ONLY)

Check in TopBar it says: "Trading Hours: 09:15 - 15:30 IST"
```

### 3. **Exit Order Verification** (CRITICAL)
```
BEFORE going live:

1. Start bot in PAPER mode
2. Take 5 test trades
3. Manually close 2-3 positions
4. Check LOGS:
   - Should see "✓ EXIT order PLACED"
   - Should see "✓ EXIT order FILLED"
   - If NOT, DO NOT GO LIVE

Log should show:
[ORDER] ✓ EXIT order PLACED | OrderID: xxx
[ORDER] ✓ EXIT order FILLED | Average Price: xxx
```

### 4. **Check Dhan Credentials**
```
Settings → API Credentials
- Verify Access Token is correct
- Verify Client ID is correct
- Test with a ₹100 paper trade first

If connection fails = DO NOT GO LIVE
```

### 5. **Verify Position Sizing**
```
Settings → Risk Parameters
- Order Qty: Should be 1-2 (start small!)
- Daily Max Loss: Set reasonable (₹5000 for first day?)
- Initial SL: 50 points (standard)
- Trailing: 10 points start, 5 points step

DO NOT use large position sizes on first day!
```

---

## 🔒 SAFETY FEATURES ENABLED

✅ **Double Market Check**
- Frontend shows market status with IST time
- Backend validates market is open before entry
- Extra validation in enter_position() function

✅ **Entry Blocking**
- Trades blocked if market closed
- Trades blocked if outside 9:15-3:20 AM
- Auto squareoff at 3:25 PM

✅ **Exit Verification**
- Explicit order placement confirmation
- Wait for fill verification
- Clear logging of success/failure

✅ **Risk Protection**
- Daily max loss trigger
- Per-trade max loss limit
- Position sizing by risk

---

## 📋 TODAY'S ACTION ITEMS

### Step 1: Test Frontend Display (5 min)
```
□ Hard refresh browser (Ctrl+Shift+R)
□ Check TopBar shows "🔴 CLOSED" right now
□ If shows "🟢 OPEN" at 8:00 AM = PROBLEM
□ Screenshot the market status for reference
```

### Step 2: Verify Logs (5 min)
```
□ Check backend logs: backend/logs/bot.log
□ Verify date is today, Jan 29, 2026
□ Logs should show market status checks
```

### Step 3: Paper Trading Test (15 min)
```
□ Set Mode to PAPER
□ Start bot
□ Wait for signal
□ Take 3-5 test trades
□ Close them manually
□ Check all closed with exit orders logged
□ Verify analytics shows all trades
```

### Step 4: Verify Exit Orders (10 min)
```
□ In paper trades, look for:
  ✓ "[ORDER] Exit order placed"
  ✓ "[ORDER] Exit order FILLED"
□ If missing = DO NOT GO LIVE
□ Contact support if issue found
```

### Step 5: Tomorrow Morning Pre-Launch
```
□ Check market status at 9:10 AM
□ Should show "🟢 OPEN"
□ Check logs are clean
□ Verify credentials still valid
□ Switch to LIVE mode
□ Start bot
□ Monitor first 10 trades carefully
```

---

## ⛔ DO NOT GO LIVE IF:

- [ ] Market status shows OPEN when market is CLOSED
- [ ] Exit orders not showing in logs
- [ ] Dhan connection says "disconnected"
- [ ] Any trades fail to close
- [ ] Analytics not showing trades
- [ ] Position sizing seems too large
- [ ] You're nervous or unsure

---

## ✅ GO LIVE ONLY IF:

- [x] Market status is CORRECT (shows actual time)
- [x] Exit orders working (clear logs)
- [x] Paper trades successful (5+ test trades)
- [x] Dhan connection stable
- [x] Position size is small (1-2 lots max)
- [x] Daily loss limit set conservatively
- [x] You've read all logs and understand them
- [x] You're ready to monitor actively

---

## 📞 SUPPORT

**If market status still wrong**:
1. Hard refresh: `Ctrl + Shift + R`
2. Check backend logs for time
3. Verify IST time matches your system
4. If still wrong → DO NOT GO LIVE, contact support

**If exit orders not logging**:
1. Check logs in `backend/logs/bot.log`
2. Look for "[ORDER]" messages
3. Should see BOTH "placed" and "filled"
4. If missing → DO NOT GO LIVE

**General Issues**:
- Check `IMPLEMENTATION_SUMMARY.md`
- Review `ANALYTICS_GUIDE.md`
- Check logs first, then support

---

## 🎯 First Day Plan (Tomorrow)

```
9:00 AM IST
  ├─ Check market status (should be 🟢 OPEN)
  ├─ Verify Dhan connection
  ├─ Review logs for any errors
  └─ Ready to start

9:15 AM IST (Market Opens)
  ├─ Start bot
  ├─ Monitor first 2-3 trades closely
  ├─ Watch exit orders go through
  ├─ Check analytics dashboard
  └─ Verify PnL calculation

Throughout Day:
  ├─ Keep eye on market status
  ├─ Monitor daily PnL
  ├─ Check for any order failures
  └─ Review logs every hour

3:20 PM IST
  ├─ Stop accepting new entries
  ├─ Let existing positions close
  └─ Archive today's logs

3:30 PM IST
  ├─ Market closes
  ├─ Auto squareoff any open positions
  └─ Final PnL check
```

---

## 🚀 You're Ready!

All safety features are in place:
1. ✅ Market status validation
2. ✅ Entry blocking when closed
3. ✅ Exit order verification
4. ✅ Risk protection
5. ✅ Detailed logging

**Just follow the checklist above, and you'll be safe!**

Good luck tomorrow! 🎯

---

**Created**: January 29, 2026
**For**: Tomorrow's Live Trading
**Status**: Ready for Deployment

