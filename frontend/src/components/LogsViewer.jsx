import React, { useContext, useState, useEffect, useMemo, useRef } from "react";
import axios from "axios";
import { AppContext } from "@/App";
import { API } from "@/App";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RefreshCw, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const LogsViewer = () => {
  const { logs, refreshLogs, config } = useContext(AppContext);
  const [filter, setFilter] = useState("all");
  const [strategyFilter, setStrategyFilter] = useState("all");
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef(null);

  const portfolioIds = useMemo(() => {
    const raw = config?.portfolio_strategy_ids;
    if (!Array.isArray(raw)) return [];
    const out = [];
    const seen = new Set();
    for (const x of raw) {
      const n = Number(x);
      if (!Number.isFinite(n)) continue;
      const id = Math.trunc(n);
      if (id <= 0 || seen.has(id)) continue;
      seen.add(id);
      out.push(id);
    }
    return out;
  }, [config?.portfolio_strategy_ids]);

  const [strategies, setStrategies] = useState([]);
  useEffect(() => {
    let cancelled = false;
    if (!config?.portfolio_enabled || portfolioIds.length === 0) {
      setStrategies([]);
      return;
    }
    (async () => {
      try {
        const res = await axios.get(`${API}/strategies`);
        if (cancelled) return;
        setStrategies(Array.isArray(res.data) ? res.data : []);
      } catch {
        if (cancelled) return;
        setStrategies([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [config?.portfolio_enabled, portfolioIds.join(",")]);

  const nameById = useMemo(() => {
    const m = new Map();
    for (const s of strategies || []) {
      const id = Number(s?.id);
      if (Number.isFinite(id)) m.set(Math.trunc(id), String(s?.name || ""));
    }
    return m;
  }, [strategies]);

  // Refresh logs when filters change
  useEffect(() => {
    const strategyId = strategyFilter !== "all" ? Number(strategyFilter) : null;
    const level = filter;
    refreshLogs({ limit: 200, level, strategyId });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, strategyFilter]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter((log) => {
    if (filter !== "all" && log.level !== filter.toUpperCase()) return false;
    if (strategyFilter !== "all") {
      const tag = `[STRAT:${strategyFilter}]`;
      if (!String(log.message || "").includes(tag)) return false;
    }
    return true;
  });

  const getLevelClass = (level) => {
    switch (level?.toUpperCase()) {
      case "INFO":
        return "log-info";
      case "WARNING":
      case "WARN":
        return "log-warn";
      case "ERROR":
        return "log-error";
      default:
        return "text-gray-600";
    }
  };

  const getLevelBadge = (level) => {
    const baseClass = "px-1.5 py-0.5 rounded text-[10px] font-bold uppercase";
    switch (level?.toUpperCase()) {
      case "INFO":
        return `${baseClass} bg-blue-100 text-blue-700`;
      case "WARNING":
      case "WARN":
        return `${baseClass} bg-amber-100 text-amber-700`;
      case "ERROR":
        return `${baseClass} bg-red-100 text-red-700`;
      default:
        return `${baseClass} bg-gray-100 text-gray-700`;
    }
  };

  return (
    <div className="terminal-card flex-1" data-testid="logs-viewer">
      <div className="terminal-card-header">
        <h2 className="text-sm font-semibold text-gray-900 font-[Manrope]">
          Bot Logs
        </h2>
        <div className="flex items-center gap-2">
          {config?.portfolio_enabled && portfolioIds.length > 0 ? (
            <Select value={strategyFilter} onValueChange={setStrategyFilter}>
              <SelectTrigger className="h-7 w-44 text-xs rounded-sm">
                <SelectValue placeholder="Strategy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All strategies</SelectItem>
                {portfolioIds.map((id) => (
                  <SelectItem key={id} value={String(id)}>
                    {(nameById.get(id) || `Strategy ${id}`) + ` (ID: ${id})`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : null}
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="h-7 w-24 text-xs rounded-sm">
              <Filter className="w-3 h-3 mr-1" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="info">Info</SelectItem>
              <SelectItem value="warn">Warn</SelectItem>
              <SelectItem value="error">Error</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              refreshLogs({
                limit: 200,
                level: filter,
                strategyId: strategyFilter !== "all" ? Number(strategyFilter) : null,
              })
            }
            className="h-7 w-7 p-0 rounded-sm"
            data-testid="refresh-logs-btn"
          >
            <RefreshCw className="w-3 h-3" />
          </Button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="log-container h-[250px] overflow-y-auto"
        onMouseEnter={() => setAutoScroll(false)}
        onMouseLeave={() => setAutoScroll(true)}
      >
        {filteredLogs.length > 0 ? (
          filteredLogs.map((log, index) => (
            <div
              key={index}
              className="log-entry py-1 flex items-start gap-2"
              data-testid={`log-entry-${index}`}
            >
              <span className="text-gray-400 shrink-0">
                {log.timestamp?.split(" ")[1]?.split(",")[0] || ""}
              </span>
              <span className={getLevelBadge(log.level)}>{log.level}</span>
              <span className={`flex-1 ${getLevelClass(log.level)}`}>
                {log.message}
              </span>
            </div>
          ))
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400 text-sm">
            No logs available
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
        <span>{filteredLogs.length} entries</span>
        <span
          className={`cursor-pointer ${
            autoScroll ? "text-blue-600" : "text-gray-400"
          }`}
          onClick={() => setAutoScroll(!autoScroll)}
        >
          Auto-scroll: {autoScroll ? "ON" : "OFF"}
        </span>
      </div>
    </div>
  );
};

export default LogsViewer;
