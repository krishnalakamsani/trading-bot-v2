import React, { useContext, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { API, AppContext } from "@/App";
import { Layers } from "lucide-react";

const RunningStrategiesPanel = () => {
  const { config, timeframes, botStatus, fetchData, portfolioPositions, portfolioStrategiesState, startBot } = useContext(AppContext);

  const indexOptions = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"];

  const portfolioEnabled = !!config?.portfolio_enabled;
  const portfolioIdsRaw = Array.isArray(config?.portfolio_strategy_ids)
    ? config.portfolio_strategy_ids
    : [];

  const portfolioIds = useMemo(() => {
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

  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const shouldFetch = portfolioEnabled;
    if (!shouldFetch) {
      setStrategies([]);
      setLoadError(null);
      setLoading(false);
      return;
    }

    (async () => {
      try {
        setLoading(true);
        setLoadError(null);
        const res = await axios.get(`${API}/strategies`);
        if (cancelled) return;
        setStrategies(Array.isArray(res.data) ? res.data : []);
      } catch (e) {
        if (cancelled) return;
        setLoadError("Unable to load strategies");
      } finally {
        if (cancelled) return;
        setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [portfolioEnabled]);

  const strategyById = useMemo(() => {
    const map = new Map();
    for (const s of strategies || []) {
      const id = Number(s?.id);
      if (Number.isFinite(id)) {
        map.set(id, s);
      }
    }
    return map;
  }, [strategies]);

  const knownStrategyIds = useMemo(() => {
    const set = new Set();
    for (const s of strategies || []) {
      const id = Number(s?.id);
      if (Number.isFinite(id) && id > 0) set.add(Math.trunc(id));
    }
    return set;
  }, [strategies]);

  const displayIds = useMemo(() => {
    if (!portfolioEnabled) return [];
    if (loading || loadError) return portfolioIds;
    return Array.from(knownStrategyIds).sort((a, b) => a - b);
  }, [portfolioEnabled, portfolioIds, loading, loadError, knownStrategyIds]);

  const strategyCount = portfolioEnabled ? displayIds.length : 1;

  const instances = useMemo(() => {
    return config?.portfolio_instances && typeof config.portfolio_instances === "object"
      ? config.portfolio_instances
      : {};
  }, [config?.portfolio_instances]);

  const [draftById, setDraftById] = useState({});
  const [savingById, setSavingById] = useState({});
  const [saveErrorById, setSaveErrorById] = useState({});
  const [expandedById, setExpandedById] = useState({});

  const stratStateById = useMemo(() => {
    const map = new Map();
    for (const s of portfolioStrategiesState || []) {
      const id = Number(s?.strategy_id);
      if (!Number.isFinite(id)) continue;
      map.set(String(Math.trunc(id)), s);
    }
    return map;
  }, [portfolioStrategiesState]);

  const fmtClock = (iso) => {
    if (!iso) return "—";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  const isRecent = (iso, seconds) => {
    if (!iso) return false;
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return false;
    return Date.now() - d.getTime() <= seconds * 1000;
  };

  useEffect(() => {
    if (!portfolioEnabled) {
      setDraftById({});
      return;
    }

    const next = {};
    for (const id of displayIds) {
      const key = String(id);
      const inst = instances?.[key] && typeof instances[key] === "object" ? instances[key] : {};
      next[key] = {
        active: inst.active !== false,
        mode: (inst.mode || "paper").toLowerCase() === "live" ? "live" : "paper",
        selected_index: String(inst.selected_index || config?.selected_index || "NIFTY").toUpperCase(),
        candle_interval: Number.isFinite(Number(inst.candle_interval))
          ? String(Math.max(1, Math.trunc(Number(inst.candle_interval))))
          : String(config?.candle_interval ?? 5),
        order_qty: Number.isFinite(Number(inst.order_qty))
          ? String(Math.max(0, Math.trunc(Number(inst.order_qty))))
          : String(config?.order_qty ?? 1),
        target_points: Number.isFinite(Number(inst.target_points))
          ? String(Number(inst.target_points))
          : String(config?.target_points ?? 0),
        initial_stoploss: Number.isFinite(Number(inst.initial_stoploss))
          ? String(Number(inst.initial_stoploss))
          : String(config?.initial_stoploss ?? 0),
        trail_start_profit: Number.isFinite(Number(inst.trail_start_profit))
          ? String(Number(inst.trail_start_profit))
          : String(config?.trail_start_profit ?? 0),
        trail_step: Number.isFinite(Number(inst.trail_step))
          ? String(Number(inst.trail_step))
          : String(config?.trail_step ?? 0),
        max_loss_per_trade: Number.isFinite(Number(inst.max_loss_per_trade))
          ? String(Number(inst.max_loss_per_trade))
          : String(config?.max_loss_per_trade ?? 0),
      };
    }
    setDraftById(next);
  }, [
    portfolioEnabled,
    displayIds.join(","),
    instances,
    config?.order_qty,
    config?.target_points,
    config?.initial_stoploss,
    config?.trail_start_profit,
    config?.trail_step,
    config?.max_loss_per_trade,
  ]);

  useEffect(() => {
    if (!portfolioEnabled) {
      setExpandedById({});
      return;
    }

    setExpandedById((prev) => {
      const next = {};
      for (const id of displayIds) {
        const key = String(id);
        const already = Object.prototype.hasOwnProperty.call(prev || {}, key)
          ? !!prev[key]
          : undefined;
        const hasSaved = Object.prototype.hasOwnProperty.call(instances || {}, key);
        // Default: show editor if never saved; otherwise keep collapsed.
        next[key] = already !== undefined ? already : !hasSaved;
      }
      return next;
    });
  }, [portfolioEnabled, displayIds.join(","), instances]);

  const patchInstance = async (id, patch) => {
    const key = String(id);
    setSavingById((s) => ({ ...s, [key]: true }));
    setSaveErrorById((e) => ({ ...e, [key]: null }));
    try {
      await axios.patch(`${API}/portfolio/strategies/${id}/instance`, patch);
      await fetchData();
      return true;
    } catch (e) {
      const msg = e?.response?.data?.detail || "Failed to update";
      setSaveErrorById((prev) => ({ ...prev, [key]: msg }));
      return false;
    } finally {
      setSavingById((s) => ({ ...s, [key]: false }));
    }
  };

  const saveRow = async (id) => {
    const key = String(id);
    const d = draftById?.[key];
    if (!d) return;
    const ok = await patchInstance(id, {
      active: d.active !== false,
      mode: d.mode === "live" ? "live" : "paper",
      selected_index: String(d.selected_index || config?.selected_index || "NIFTY").toUpperCase(),
      candle_interval: Math.max(1, Math.trunc(Number(d.candle_interval || 0))),
      order_qty: Math.max(0, Math.trunc(Number(d.order_qty || 0))),
      target_points: Number(d.target_points || 0),
      initial_stoploss: Number(d.initial_stoploss || 0),
      trail_start_profit: Number(d.trail_start_profit || 0),
      trail_step: Number(d.trail_step || 0),
      max_loss_per_trade: Number(d.max_loss_per_trade || 0),
    });

    if (ok) {
      setExpandedById((prev) => ({ ...prev, [key]: false }));
    }
  };

  const squareOffStrategy = async (id) => {
    try {
      await axios.post(`${API}/portfolio/strategies/${id}/squareoff`);
      await fetchData();
    } catch (e) {
      const msg = e?.response?.data?.detail || "Square-off failed";
      setSaveErrorById((prev) => ({ ...prev, [String(id)]: msg }));
    }
  };

  return (
    <div className="terminal-card" data-testid="running-strategies">
      <div className="terminal-card-header">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-600" />
          <h2 className="text-sm font-semibold text-gray-900 font-[Manrope]">
            Running Strategies
          </h2>
        </div>
        <span className="text-xs text-gray-500 font-mono">
          {portfolioEnabled ? `${strategyCount} selected` : "single"}
        </span>
      </div>

      <div className="p-4">
        {portfolioEnabled ? (
          <div className="space-y-2">
            {displayIds.length === 0 ? (
              <div className="text-sm text-gray-500">No strategies selected</div>
            ) : (
              <>
                {loading && (
                  <div className="text-sm text-gray-500">Loading strategies…</div>
                )}
                {loadError && (
                  <div className="text-sm text-gray-500">{loadError}</div>
                )}

                <div className="space-y-2">
                  {displayIds.map((id) => {
                    const meta = strategyById.get(Number(id));
                    const name = meta?.name || `Strategy ${id}`;
                    const key = String(id);
                    const draft = draftById?.[key] || {
                      active: true,
                      mode: "paper",
                      selected_index: String(config?.selected_index || "NIFTY").toUpperCase(),
                      order_qty: String(config?.order_qty ?? 1),
                      target_points: String(config?.target_points ?? 0),
                      initial_stoploss: String(config?.initial_stoploss ?? 0),
                      trail_start_profit: String(config?.trail_start_profit ?? 0),
                      trail_step: String(config?.trail_step ?? 0),
                      max_loss_per_trade: String(config?.max_loss_per_trade ?? 0),
                    };
                    const isSaving = !!savingById?.[key];
                    const err = saveErrorById?.[key];

                    const expanded = !!expandedById?.[key];
                    const hasOpenPosition = Array.isArray(portfolioPositions)
                      ? portfolioPositions.some((p) => String(p?.strategy_id) === String(id))
                      : false;

                    const statusText = botStatus?.is_running
                      ? (draft.active !== false ? "RUNNING" : "PAUSED")
                      : "READY";

                    const summary = `idx=${draft.selected_index} tf=${draft.candle_interval || (config?.candle_interval ?? 5)}s mode=${draft.mode} lots=${draft.order_qty} tgt=${draft.target_points} sl=${draft.initial_stoploss} trail=${draft.trail_start_profit}/${draft.trail_step} maxLoss=${draft.max_loss_per_trade}`;

                    const state = stratStateById.get(key);
                    const lastEval = state?.last_eval_time_utc;
                    const lastAction = state?.last_action;
                    const lastActionTime = state?.last_action_time_utc;
                    const lastReason = state?.last_action_reason;
                    const calcOk = botStatus?.is_running && isRecent(lastEval, Math.max(5, Number(config?.candle_interval || 5) * 2));

                    const activityLine = `calc=${calcOk ? "YES" : "NO"} lastEval=${fmtClock(lastEval)} last=${lastAction ? `${lastAction}@${fmtClock(lastActionTime)}` : "—"}${lastReason ? ` (${lastReason})` : ""}`;
                    return (
                      <div
                        key={id}
                        className="bg-gray-50 rounded-sm p-2 border border-gray-100"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="text-sm font-medium text-gray-900 truncate">
                              {name}
                            </div>
                            <div className="text-xs text-gray-500 font-mono">ID: {id}</div>
                            <div className="text-xs text-gray-500 font-mono truncate mt-0.5">
                              {summary}
                            </div>
                            <div className="text-xs font-mono truncate mt-0.5">
                              <span className={calcOk ? "text-emerald-700" : "text-gray-500"}>
                                {activityLine}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <div
                              className={`text-xs font-medium ${
                                statusText === "RUNNING"
                                  ? "text-emerald-700"
                                  : statusText === "PAUSED"
                                  ? "text-amber-700"
                                  : "text-gray-500"
                              }`}
                            >
                              {statusText}
                            </div>

                            <button
                              className="text-xs px-2 py-1 rounded-sm border border-gray-200 bg-white text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                              disabled={isSaving}
                              onClick={() =>
                                setExpandedById((prev) => ({ ...prev, [key]: !expanded }))
                              }
                              title={expanded ? "Hide settings" : "Edit settings"}
                            >
                              {expanded ? "Hide" : "Edit"}
                            </button>

                            <button
                              className="text-xs px-2 py-1 rounded-sm border border-gray-200 bg-white text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                              disabled={isSaving}
                              onClick={async () => {
                                const enable = draft.active === false;
                                const ok = await patchInstance(id, { active: enable });
                                if (ok && enable && !botStatus?.is_running) {
                                  await startBot();
                                }
                              }}
                              title="Start/stop this strategy without affecting others"
                            >
                              {draft.active !== false ? "Stop" : "Start"}
                            </button>

                            <button
                              className="text-xs px-2 py-1 rounded-sm border border-gray-200 bg-white text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                              disabled={isSaving || !hasOpenPosition}
                              onClick={() => squareOffStrategy(id)}
                              title={hasOpenPosition ? "Square off this strategy's open position" : "No open position"}
                            >
                              Square Off
                            </button>
                          </div>
                        </div>

                        {expanded ? (
                          <>
                        <div className="mt-2 grid grid-cols-2 lg:grid-cols-8 gap-2">
                          <div>
                            <div className="text-[10px] text-gray-500">Mode</div>
                            <select
                              className="w-full text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                              value={draft.mode}
                              onChange={(e) =>
                                setDraftById((prev) => ({
                                  ...prev,
                                  [key]: { ...draft, mode: e.target.value },
                                }))
                              }
                              disabled={isSaving}
                            >
                              <option value="paper">paper</option>
                              <option value="live">live</option>
                            </select>
                          </div>

                          <div>
                            <div className="text-[10px] text-gray-500">Index</div>
                            <select
                              className="w-full text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                              value={draft.selected_index}
                              onChange={(e) =>
                                setDraftById((prev) => ({
                                  ...prev,
                                  [key]: { ...draft, selected_index: e.target.value },
                                }))
                              }
                              disabled={isSaving}
                            >
                              {indexOptions.map((x) => (
                                <option key={x} value={x}>
                                  {x}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <div className="text-[10px] text-gray-500">Timeframe</div>
                            <select
                              className="w-full text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                              value={String(draft.candle_interval || config?.candle_interval || 5)}
                              onChange={(e) =>
                                setDraftById((prev) => ({
                                  ...prev,
                                  [key]: { ...draft, candle_interval: e.target.value },
                                }))
                              }
                              disabled={isSaving}
                            >
                              {(timeframes || [
                                { value: 5, label: "5 seconds" },
                                { value: 15, label: "15 seconds" },
                                { value: 30, label: "30 seconds" },
                                { value: 60, label: "1 minute" },
                                { value: 300, label: "5 minutes" },
                                { value: 900, label: "15 minutes" },
                              ]).map((tf) => (
                                <option key={tf.value} value={String(tf.value)}>
                                  {tf.label}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <div className="text-[10px] text-gray-500">Lots</div>
                            <input
                              className="w-full text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                              value={draft.order_qty}
                              onChange={(e) =>
                                setDraftById((prev) => ({
                                  ...prev,
                                  [key]: { ...draft, order_qty: e.target.value },
                                }))
                              }
                              disabled={isSaving}
                            />
                          </div>

                          <div>
                            <div className="text-[10px] text-gray-500">Target</div>
                            <input
                              className="w-full text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                              value={draft.target_points}
                              onChange={(e) =>
                                setDraftById((prev) => ({
                                  ...prev,
                                  [key]: { ...draft, target_points: e.target.value },
                                }))
                              }
                              disabled={isSaving}
                            />
                          </div>

                          <div>
                            <div className="text-[10px] text-gray-500">SL</div>
                            <input
                              className="w-full text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                              value={draft.initial_stoploss}
                              onChange={(e) =>
                                setDraftById((prev) => ({
                                  ...prev,
                                  [key]: { ...draft, initial_stoploss: e.target.value },
                                }))
                              }
                              disabled={isSaving}
                            />
                          </div>

                          <div>
                            <div className="text-[10px] text-gray-500">Trail (start/step)</div>
                            <div className="flex gap-1">
                              <input
                                className="w-1/2 text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                                value={draft.trail_start_profit}
                                onChange={(e) =>
                                  setDraftById((prev) => ({
                                    ...prev,
                                    [key]: { ...draft, trail_start_profit: e.target.value },
                                  }))
                                }
                                disabled={isSaving}
                              />
                              <input
                                className="w-1/2 text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                                value={draft.trail_step}
                                onChange={(e) =>
                                  setDraftById((prev) => ({
                                    ...prev,
                                    [key]: { ...draft, trail_step: e.target.value },
                                  }))
                                }
                                disabled={isSaving}
                              />
                            </div>
                          </div>

                          <div>
                            <div className="text-[10px] text-gray-500">Max Loss</div>
                            <input
                              className="w-full text-xs border border-gray-200 rounded-sm bg-white px-2 py-1"
                              value={draft.max_loss_per_trade}
                              onChange={(e) =>
                                setDraftById((prev) => ({
                                  ...prev,
                                  [key]: { ...draft, max_loss_per_trade: e.target.value },
                                }))
                              }
                              disabled={isSaving}
                            />
                          </div>
                        </div>

                        <div className="mt-2 flex items-center justify-between">
                          <div className="text-xs text-gray-500">
                            {err ? <span className="text-red-600">{err}</span> : null}
                          </div>
                          <button
                            className="text-xs px-2 py-1 rounded-sm border border-gray-200 bg-white text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                            onClick={() => saveRow(id)}
                            disabled={isSaving}
                          >
                            {isSaving ? "Saving…" : "Save"}
                          </button>
                        </div>
                          </>
                        ) : (
                          err ? (
                            <div className="mt-2 text-xs text-red-600">{err}</div>
                          ) : null
                        )}
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-1">
            <div className="text-sm text-gray-900 font-medium">
              Single strategy mode
            </div>
            <div className="text-xs text-gray-500 font-mono">
              {String(config?.indicator_type || "—")}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RunningStrategiesPanel;
