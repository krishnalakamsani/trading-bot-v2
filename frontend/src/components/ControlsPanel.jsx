import React, { useContext, useState } from "react";
import { AppContext } from "@/App";
import { Play, Square } from "lucide-react";
import { Button } from "@/components/ui/button";

const ControlsPanel = () => {
  const { 
    botStatus, 
    startBot, 
    stopBot, 
  } = useContext(AppContext);
  
  const [loading, setLoading] = useState({
    start: false,
    stop: false,
  });

  const handleStart = async () => {
    setLoading((prev) => ({ ...prev, start: true }));
    try {
      await startBot();
    } finally {
      setLoading((prev) => ({ ...prev, start: false }));
    }
  };

  const handleStop = async () => {
    setLoading((prev) => ({ ...prev, stop: true }));
    try {
      await stopBot();
    } finally {
      setLoading((prev) => ({ ...prev, stop: false }));
    }
  };

  return (
    <div className="terminal-card" data-testid="controls-panel">
      <div className="terminal-card-header">
        <h2 className="text-sm font-semibold text-gray-900 font-[Manrope]">
          Controls
        </h2>
      </div>

      <div className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <Button
            onClick={handleStart}
            disabled={loading.start || botStatus.is_running}
            size="sm"
            className="rounded-sm btn-active"
            data-testid="start-bot-btn"
          >
            <Play className="w-3 h-3 mr-1" />
            {loading.start ? "Starting..." : "Start"}
          </Button>

          <Button
            onClick={handleStop}
            disabled={loading.stop || !botStatus.is_running}
            size="sm"
            variant="outline"
            className="rounded-sm"
            data-testid="stop-bot-btn"
          >
            <Square className="w-3 h-3 mr-1" />
            {loading.stop ? "Stopping..." : "Stop"}
          </Button>
        </div>

        <div className="text-xs text-gray-500">
          Per-strategy start/stop is in Running Strategies.
        </div>
      </div>
    </div>
  );
};

export default ControlsPanel;
