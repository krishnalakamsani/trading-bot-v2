# Testing Guide - Trading Bot

## Testing Outside Market Hours

Since the market is closed, you can test all the recent changes using the built-in testing mode.

### Quick Start

1. **Open Settings Panel**
   - Click the Settings icon in the dashboard
   - Navigate to the "Testing" tab

2. **Enable Testing Mode**
   - Toggle ON "Bypass Market Hours Check"
   - Click "Save Testing Params"
   - You'll see a warning that market hours are disabled

3. **Configure Bot for Testing**
   - Ensure bot is in **Paper Mode** (very important!)
   - Set your desired index (NIFTY/BANKNIFTY)
   - Configure candle interval (5s recommended for fast testing)
   - Adjust trailing SL settings if needed

4. **Start Testing**
   - Click "Start Bot" from the main dashboard
   - Bot will start generating candles and signals immediately
   - Watch for SuperTrend signals (GREEN/RED)
   - Observe entry/exit behavior in real-time

### What Gets Tested

✅ **Entry Logic**
- SuperTrend flip detection
- Entry on signal generation
- Entry within trading hours check (bypassed in test mode)
- Position opening logic

✅ **Exit Logic**  
- Exit on opposite SuperTrend flip
- Immediate re-entry in opposite direction
- Trailing SL activation and updates
- Target hit detection

✅ **Trailing SL**
- Initial fixed SL setting
- Trail start profit trigger
- Step-based trailing logic
- Complete disable when set to 0

✅ **Analysis Page**
- Date range filtering
- Daily performance breakdown
- Exit reason analysis
- All filter options

### Testing Scenarios

#### Test 1: Entry on Signal Flip
1. Start bot in Paper mode with bypass enabled
2. Wait for first SuperTrend signal
3. Verify entry is taken immediately
4. Check logs for entry confirmation

#### Test 2: Exit and Reverse
1. Have open CE position
2. Wait for SuperTrend to flip RED
3. Verify:
   - CE position exits
   - PE position enters immediately
4. Check position panel shows PE

#### Test 3: Trailing SL Disabled
1. Set trail_start_profit = 0 or trail_step = 0
2. Take a position
3. Verify no trailing SL is set
4. Position should stay open until signal flip

#### Test 4: Analysis Filters
1. Generate some test trades
2. Go to Analysis page
3. Test date range filters (Today, Last 7 Days, etc.)
4. Test option type filters (CE/PE)
5. Test exit reason filters
6. Verify statistics update correctly

### Important Notes

⚠️ **Safety First**
- Always use Paper Mode when testing
- Never enable bypass mode in Live trading
- Disable bypass after testing is complete

📊 **Market Data**
- In Paper mode, option prices are simulated
- Index LTP may be stale (last closing price)
- Signals are generated based on simulated candles

🔄 **Restart After Changes**
- Backend changes require container restart
- Frontend changes: rebuild and restart frontend container
- Config changes: save from UI (no restart needed)

### Disabling Test Mode

When done testing:
1. Go to Settings → Testing tab
2. Toggle OFF "Bypass Market Hours Check"
3. Click "Save Testing Params"
4. Bot will respect normal market hours (9:15 AM - 3:30 PM IST)

### Deployment Commands

```bash
# Restart backend with changes
docker-compose restart backend

# Rebuild and restart frontend
docker-compose build frontend
docker-compose up -d frontend

# View logs
docker logs -f niftyalgo-backend
docker logs -f niftyalgo-frontend
```

### Troubleshooting

**Bot won't start:**
- Check bypass_market_hours is enabled in config
- Verify Paper mode is selected
- Check backend logs for errors

**No signals generated:**
- Ensure candle interval is short (5s or 15s)
- Wait for initial indicator warmup period
- Check SuperTrend/MACD parameters

**Positions not entering:**
- Verify bypass_market_hours = true
- Check max_trades_per_day limit
- Review entry_hours protection

**Trailing SL not working:**
- Check trail_start_profit and trail_step are > 0
- Verify profit has reached trail_start threshold
- Check logs for SL updates

---

Happy Testing! 🚀
