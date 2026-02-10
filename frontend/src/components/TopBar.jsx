import React, { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AppContext } from "@/App";
import { Settings, Wifi, WifiOff, TrendingUp, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";

const TopBar = ({ onSettingsClick }) => {
  const { botStatus, wsConnected, config } = useContext(AppContext);
  const navigate = useNavigate();

  const portfolioEnabled = !!config?.portfolio_enabled;
  const portfolioIdsRaw = Array.isArray(config?.portfolio_strategy_ids)
    ? config.portfolio_strategy_ids
    : [];

  const portfolioIds = React.useMemo(() => {
    const seen = new Set();
    const ids = [];
    for (const x of portfolioIdsRaw) {
      const n = Number(x);
      if (!Number.isFinite(n)) continue;
      const id = Math.trunc(n);
      if (id <= 0) continue;
      if (seen.has(id)) continue;
      seen.add(id);
      ids.push(id);
    }
    return ids;
  }, [portfolioIdsRaw]);

  const activePortfolioIds = React.useMemo(() => {
    if (!portfolioEnabled) return [];
    const inst = config?.portfolio_instances && typeof config.portfolio_instances === "object"
      ? config.portfolio_instances
      : {};
    return (portfolioIds || []).filter((id) => {
      const key = String(id);
      const cfg = inst?.[key];
      if (!cfg || typeof cfg !== "object") return true;
      return cfg.active !== false;
    });
  }, [portfolioEnabled, portfolioIds, config?.portfolio_instances]);

  const strategyCount = portfolioEnabled ? activePortfolioIds.length : 1;

  return (
    <div
      className="bg-white border-b border-gray-200 px-4 lg:px-6 py-3 flex items-center justify-between"
      data-testid="top-bar"
    >
      {/* Left - Logo & Title */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-sm flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 className="text-base font-semibold text-gray-900 font-[Manrope] tracking-tight">
            SuperTrend Bot
          </h1>
          <p className="text-xs text-gray-500">
            {config.selected_index || "NIFTY"} Options Trading
          </p>
        </div>
      </div>

      {/* Center - Status Indicators */}
      <div className="hidden md:flex items-center gap-4">
        {/* Bot Status */}
        <div
          className={`status-badge ${
            botStatus.is_running ? "status-running" : "status-stopped"
          }`}
          data-testid="bot-status-badge"
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              botStatus.is_running ? "bg-emerald-500" : "bg-gray-400"
            }`}
          />
          {botStatus.is_running ? "Running" : "Stopped"}
        </div>

        {/* Strategies Count */}
        <div
          className="status-badge status-info"
          data-testid="strategies-badge"
          title={
            portfolioEnabled
              ? `Portfolio enabled. Active strategy IDs: ${(activePortfolioIds || []).join(", ") || "—"}`
              : "Single strategy mode"
          }
        >
          {portfolioEnabled ? "STRATS" : "STRAT"}: {strategyCount}
        </div>

        {/* Market Status - PROMINENT */}
        <div
          className={`status-badge ${
            botStatus.market_status === "open" ? "status-running" : "status-error"
          }`}
          data-testid="market-status-badge"
          title={botStatus.market_details ? `${botStatus.market_details.current_time_ist} IST` : ""}
        >
          <span className={`w-2 h-2 rounded-full ${
            botStatus.market_status === "open" ? "bg-emerald-500 animate-pulse" : "bg-red-500"
          }`} />
          <span className="font-semibold">
            {botStatus.market_status === "open" ? "🟢 OPEN" : "🔴 CLOSED"}
          </span>
          {botStatus.market_details && (
            <span className="text-xs opacity-70 ml-1">
              {botStatus.market_details.current_time_ist}
            </span>
          )}
        </div>

        {/* Connection Status */}
        <div
          className={`status-badge ${
            wsConnected ? "status-running" : "status-error"
          }`}
          data-testid="ws-status-badge"
        >
          {wsConnected ? (
            <Wifi className="w-3 h-3" />
          ) : (
            <WifiOff className="w-3 h-3" />
          )}
          {wsConnected ? "Connected" : "Disconnected"}
        </div>
      </div>

      {/* Right - Settings & Analysis Buttons */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/analysis')}
          className="rounded-sm btn-active hidden sm:flex"
          data-testid="analysis-btn"
          title="View trade analysis and statistics"
        >
          <BarChart3 className="w-4 h-4 mr-1" />
          Analysis
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onSettingsClick}
          className="rounded-sm btn-active"
          data-testid="settings-btn"
        >
          <Settings className="w-4 h-4 mr-1" />
          Settings
        </Button>
      </div>
    </div>
  );
};

export default TopBar;
