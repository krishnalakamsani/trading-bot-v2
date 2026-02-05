# Analytics Page Not Loading

## Root Cause
If the database file (`trading.db`) was deleted, the analytics page will fail because:
1. Database has no tables
2. Backend `/api/analytics` endpoint returns no data or errors
3. Frontend can't render empty analytics

## Solution

### Automatic (Recommended)
Just **start the backend normally**:
```bash
python backend/server.py
```

The `init_db()` function will automatically:
1. Create `trading.db` if it doesn't exist
2. Create all 4 tables: `trades`, `daily_stats`, `config`, `candle_data`
3. Backend is then ready to use

### Manual Database Initialization
If you want to explicitly initialize:
```bash
python init_database.py
```

This will:
- Create the database file
- Initialize the schema
- Show confirmation message

## What to Expect

### Empty Database (No Trades Yet)
- Analytics page will load ✓
- All metrics will show as `0` or empty
- This is **normal** before any trades are executed

### Example Response:
```json
{
  "total_trades": 0,
  "total_pnl": 0,
  "winning_trades": 0,
  "losing_trades": 0,
  "win_rate": 0,
  "trades": []
}
```

### After First Trade
Once the bot executes trades:
- Database will populate with trade data
- Analytics page will show real metrics
- Charts and statistics will display

## Verification

### Check if database is initialized:
```bash
# EC2/Linux
ls -la backend/trading.db

# Windows
dir backend\trading.db
```

### Test API endpoint:
```bash
curl http://localhost:8001/api/analytics
# Should return JSON with analytics data
```

### Check frontend shows data:
1. Open browser: `http://<your-ip>`
2. Navigate to "Trade Analysis" tab
3. Should show analytics dashboard (may be empty if no trades)

## Troubleshooting

### Database still not creating?
1. Check backend has write permission to `backend/` directory
2. Check backend process is running: `ps aux | grep server.py`
3. Check backend logs for errors
4. Manually run: `python init_database.py` to see detailed error

### Analytics page still showing error?
1. Check browser console (F12) for JavaScript errors
2. Check backend logs for API errors
3. Test with curl: `curl http://localhost:8001/api/analytics`
4. Ensure backend URL is configured correctly in frontend

### Database file exists but tables missing?
1. Delete the file: `rm backend/trading.db` (or delete it manually on Windows)
2. Restart backend to recreate schema
3. Verify with: `python init_database.py`

## Database Schema

The bot uses SQLite with 4 tables:

### trades
- All executed trades with entry/exit prices and PnL
- Used for analytics and trade history

### daily_stats  
- Daily summary (total trades, PnL, max drawdown)
- Used for daily performance tracking

### config
- Configuration settings (key-value pairs)
- Used for storing bot parameters

### candle_data
- Historical candle data with indicator values
- Used for backtesting and analysis

## Reset Database

To start fresh with a clean database:
```bash
# Delete the database file
rm backend/trading.db  # Linux/Mac
del backend\trading.db # Windows

# Restart backend (will recreate empty database)
python backend/server.py
```

After restart:
- Database will be recreated
- All tables will be empty
- Bot is ready to start fresh trading
