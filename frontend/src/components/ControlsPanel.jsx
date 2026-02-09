import React, { useContext, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { API, AppContext } from "@/App";
import { Play, Square, XCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const ControlsPanel = () => {
  const { 
    botStatus, 
    position, 
    config, 
    indices, 
    timeframes, 
    startBot, 
    stopBot, 
    squareOff, 
    updateConfig,
    setMode, 
    setSelectedIndex, 
    setTimeframe,
    fetchData,
  } = useContext(AppContext);
  
  const [loading, setLoading] = useState({
    start: false,
    stop: false,
    squareoff: false,
    tradingEnabled: false,
  });

  const [strategies, setStrategies] = useState([]);
  const [strategiesLoading, setStrategiesLoading] = useState(false);
  const [selectedStrategyId, setSelectedStrategyId] = useState("__current__");
  const [strategyTouched, setStrategyTouched] = useState(false);

  const portfolioIds = useMemo(() => {
    const raw = Array.isArray(config?.portfolio_strategy_ids)
      ? config.portfolio_strategy_ids
      : [];
    const seen = new Set();
    const ids = [];
    for (const x of raw) {
      const n = Number(x);
      if (!Number.isFinite(n)) continue;
      const id = Math.trunc(n);
      if (id <= 0) continue;
      if (seen.has(id)) continue;
      seen.add(id);
      ids.push(id);
    }
    return ids;
  }, [config?.portfolio_strategy_ids]);

  const instances = useMemo(() => {
    return config?.portfolio_instances && typeof config.portfolio_instances === "object"
      ? config.portfolio_instances
      : {};
  }, [config?.portfolio_instances]);

  const selectedStrategyIsSaved = selectedStrategyId !== "__current__";
  const selectedStrategyInt = selectedStrategyIsSaved ? Number(selectedStrategyId) : null;
  const selectedStrategyKey = selectedStrategyIsSaved ? String(Math.trunc(Number(selectedStrategyId))) : null;
  const selectedStrategyActive = selectedStrategyIsSaved
    ? (instances?.[selectedStrategyKey]?.active !== false)
    : null;

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        setStrategiesLoading(true);
        const res = await axios.get(`${API}/strategies`);
        if (cancelled) return;
        setStrategies(Array.isArray(res.data) ? res.data : []);
      } catch (e) {
        if (cancelled) return;
        setStrategies([]);
      } finally {
        if (cancelled) return;
        setStrategiesLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  // Default selection: if portfolio already configured, pick first saved strategy.
  useEffect(() => {
    if (!strategyTouched && !selectedStrategyIsSaved && portfolioIds.length > 0) {
      setSelectedStrategyId(String(portfolioIds[0]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [portfolioIds.join(",")]);

  const handleStart = async () => {
    setLoading((prev) => ({ ...prev, start: true }));

    try {
      if (selectedStrategyIsSaved && Number.isFinite(selectedStrategyInt) && selectedStrategyInt > 0) {
        const id = Math.trunc(selectedStrategyInt);

        // Ensure portfolio is enabled and the selected strategy is included.
        // Keep this control simple: starting from Controls runs the selected strategy.
        await updateConfig({
          portfolio_enabled: true,
          portfolio_strategy_ids: [id],
        });

        // Activate the strategy instance and set its mode based on current toggle.
        await axios.patch(`${API}/portfolio/strategies/${id}/instance`, {
          active: true,
          mode: botStatus?.mode === "live" ? "live" : "paper",
        });

        if (!botStatus.is_running) {
          await startBot();
        } else {
          await fetchData();
        }
      } else {
        // Backward-compatible: start the bot (single strategy mode)
        await startBot();
      }
    } finally {
      setLoading((prev) => ({ ...prev, start: false }));
    }
  };

  const handleStop = async () => {
    setLoading((prev) => ({ ...prev, stop: true }));
    try {
      if (selectedStrategyIsSaved && Number.isFinite(selectedStrategyInt) && selectedStrategyInt > 0) {
        const id = Math.trunc(selectedStrategyInt);
        await axios.post(`${API}/portfolio/strategies/${id}/stop`);
        await fetchData();
      } else {
        await stopBot();
      }
    } finally {
      setLoading((prev) => ({ ...prev, stop: false }));
    }
  };

  const handleSquareOff = async () => {
    setLoading((prev) => ({ ...prev, squareoff: true }));
    await squareOff();
    setLoading((prev) => ({ ...prev, squareoff: false }));
  };

  const handleModeChange = async (checked) => {
    await setMode(checked ? "live" : "paper");
  };

  const handleTradingEnabledChange = async (checked) => {
    setLoading((prev) => ({ ...prev, tradingEnabled: true }));
    await updateConfig({ trading_enabled: checked });
    setLoading((prev) => ({ ...prev, tradingEnabled: false }));
  };

  const handleIndexChange = async (value) => {
    await setSelectedIndex(value);
  };

  const handleTimeframeChange = async (value) => {
    await setTimeframe(parseInt(value));
  };

  const canChangeMode = !position?.has_position;
  const canChangeSettings = !botStatus.is_running && !position?.has_position;
  const portfolioEnabled = !!config?.portfolio_enabled;

  // Get selected index info
  const selectedIndexInfo = indices.find(i => i.name === (config.selected_index || "NIFTY")) || {};
  const getExpiryLabel = (index) => {
    if (!index.expiry_type) return "";
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    if (index.expiry_type === "weekly") {
      return `Weekly (${days[index.expiry_day]})`;
    } else {
      return `Monthly (Last ${days[index.expiry_day]})`;
    }
  };

  return (
    <div className="terminal-card" data-testid="controls-panel">
      <div className="terminal-card-header">
        <h2 className="text-sm font-semibold text-gray-900 font-[Manrope]">
          Controls
        </h2>
      </div>

      <div className="p-4 space-y-4">
        {/* Strategy Selection */}
        <div className="space-y-2">
          <Label className="text-xs font-medium text-gray-600">Strategy</Label>
          <Select
            value={selectedStrategyId}
            onValueChange={(v) => {
              setStrategyTouched(true);
              setSelectedStrategyId(v);
            }}
            disabled={strategiesLoading}
          >
            <SelectTrigger className="w-full rounded-sm" data-testid="strategy-select">
              <SelectValue placeholder={strategiesLoading ? "Loading..." : "Select Strategy"} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__current__">Use current settings</SelectItem>
              {(strategies || []).map((s) => (
                <SelectItem key={s.id} value={String(s.id)}>
                  {s.name || `Strategy ${s.id}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedStrategyIsSaved && (
            <p className="text-xs text-gray-500">
              Selected: ID {selectedStrategyKey} · {selectedStrategyActive === false ? "Paused" : "Active"}
            </p>
          )}
        </div>

        {portfolioEnabled ? (
          <div className="p-3 bg-gray-50 rounded-sm border border-gray-100">
            <p className="text-xs text-gray-600">
              Portfolio mode: set per-strategy Index &amp; Timeframe in Running Strategies.
            </p>
          </div>
        ) : (
          <>
            {/* Index Selection */}
            <div className="space-y-2">
              <Label className="text-xs font-medium text-gray-600">Index</Label>
              <Select
                value={config.selected_index || "NIFTY"}
                onValueChange={handleIndexChange}
                disabled={!canChangeSettings}
              >
                <SelectTrigger className="w-full rounded-sm" data-testid="index-select">
                  <SelectValue placeholder="Select Index" />
                </SelectTrigger>
                <SelectContent>
                  {indices.map((index) => (
                    <SelectItem key={index.name} value={index.name}>
                      <div className="flex items-center justify-between w-full">
                        <span>{index.name}</span>
                        <span className="text-xs text-gray-400 ml-2">
                          Lot: {index.lot_size}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedIndexInfo.expiry_type && (
                <p className="text-xs text-gray-500">
                  Expiry: {getExpiryLabel(selectedIndexInfo)}
                </p>
              )}
            </div>

            {/* Timeframe Selection */}
            <div className="space-y-2">
              <Label className="text-xs font-medium text-gray-600">Timeframe</Label>
              <Select
                value={String(config.candle_interval || 5)}
                onValueChange={handleTimeframeChange}
                disabled={!canChangeSettings}
              >
                <SelectTrigger className="w-full rounded-sm" data-testid="timeframe-select">
                  <SelectValue placeholder="Select Timeframe" />
                </SelectTrigger>
                <SelectContent>
                  {timeframes.map((tf) => (
                    <SelectItem key={tf.value} value={String(tf.value)}>
                      {tf.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!canChangeSettings && (
                <p className="text-xs text-amber-600">Stop bot to change settings</p>
              )}
            </div>
          </>
        )}

        {/* Start/Stop Buttons */}
        <div className="grid grid-cols-2 gap-2">
          <Button
            onClick={handleStart}
            disabled={loading.start}
            className="w-full h-10 bg-emerald-600 hover:bg-emerald-700 text-white rounded-sm btn-active"
            data-testid="start-bot-btn"
          >
            {loading.start ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Play className="w-4 h-4 mr-2" />
            )}
            Start
          </Button>

          <Button
            onClick={handleStop}
            disabled={loading.stop || (!selectedStrategyIsSaved && !botStatus.is_running)}
            variant="outline"
            className="w-full h-10 rounded-sm btn-active border-gray-300"
            data-testid="stop-bot-btn"
          >
            {loading.stop ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Square className="w-4 h-4 mr-2" />
            )}
            Stop
          </Button>
        </div>

        {/* Square Off Button */}
        <Button
          disabled={!position?.has_position || loading.squareoff}
          variant="destructive"
          className="w-full h-10 rounded-sm btn-active"
          data-testid="squareoff-btn"
          onClick={handleSquareOff}
        >
          {loading.squareoff ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <XCircle className="w-4 h-4 mr-2" />
          )}
          Square Off Now
        </Button>

        {/* Mode Toggle */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-sm border border-gray-100">
          <div>
            <Label htmlFor="mode-toggle" className="text-sm font-medium">
              Trading Mode
            </Label>
            <p className="text-xs text-gray-500">
              {canChangeMode
                ? "Switch between paper and live"
                : "Close position to change"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-medium ${
                botStatus.mode === "paper" ? "text-blue-600" : "text-gray-400"
              }`}
            >
              Paper
            </span>
            <Switch
              id="mode-toggle"
              checked={botStatus.mode === "live"}
              onCheckedChange={handleModeChange}
              disabled={!canChangeMode}
              data-testid="mode-toggle"
            />
            <span
              className={`text-xs font-medium ${
                botStatus.mode === "live" ? "text-amber-600" : "text-gray-400"
              }`}
            >
              Live
            </span>
          </div>
        </div>

        {/* Trading Enable Toggle (Pause Entries) */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-sm border border-gray-100">
          <div>
            <Label htmlFor="trading-enabled-toggle" className="text-sm font-medium">
              Take New Trades
            </Label>
            <p className="text-xs text-gray-500">
              {config?.trading_enabled === false
                ? "Paused: indicators run, no new entries"
                : "Enabled: bot can enter on signals"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500">Off</span>
            <Switch
              id="trading-enabled-toggle"
              checked={config?.trading_enabled !== false}
              onCheckedChange={handleTradingEnabledChange}
              disabled={loading.tradingEnabled}
              data-testid="trading-enabled-toggle"
            />
            <span className="text-xs font-medium text-emerald-700">On</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ControlsPanel;
