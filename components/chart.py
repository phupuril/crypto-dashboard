import tkinter as tk
from tkinter import ttk
from typing import Optional, List

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.binance_api import BinanceRESTClient


class CandleChartPanel(ttk.Frame):
    """
    Line chart from klines close prices (REST polling) + EMA signal.
    - Draw close price line
    - Draw EMA fast/slow
    - Display signal: BUY/SELL/NEUTRAL (based on EMA crossover)
    """

    def __init__(
        self,
        parent,
        client: BinanceRESTClient,
        symbol: str,
        interval: str = "1m",
        limit: int = 60,
        poll_ms: int = 10_000,
        ema_fast: int = 12,
        ema_slow: int = 26,
    ):
        super().__init__(parent, padding=12)
        self.client = client
        self.symbol = symbol.upper()
        self.interval = interval
        self.limit = limit
        self.poll_ms = poll_ms

        self.ema_fast = int(ema_fast)
        self.ema_slow = int(ema_slow)

        self._job: Optional[str] = None
        self._active = False

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Chart", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        self.info = ttk.Label(
            top,
            text=f"{self.symbol} | {self.interval} | last {self.limit}",
            font=("Arial", 10),
        )
        self.info.pack(side=tk.RIGHT)

        # status row
        row = ttk.Frame(self)
        row.pack(fill=tk.X, pady=(8, 0))

        self.status = ttk.Label(row, text="Status: Idle", font=("Arial", 9))
        self.status.pack(side=tk.LEFT)

        self.signal_label = ttk.Label(
            row,
            text="Signal: --",
            font=("Arial", 9, "bold")
        )
        self.signal_label.pack(side=tk.RIGHT)

        # matplotlib
        fig = Figure(figsize=(7, 3.6), facecolor="#111827")
        self.ax = fig.add_subplot(111)
        self.ax.set_facecolor("#111827")
        self.ax.tick_params(colors="#9ca3af")
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    # ---------- helpers ----------
    @staticmethod
    def _ema(values: np.ndarray, period: int) -> np.ndarray:
        """Compute EMA (same length as values)."""
        if len(values) == 0:
            return values
        period = max(1, int(period))
        alpha = 2.0 / (period + 1.0)

        ema = np.empty_like(values, dtype=float)
        ema[0] = values[0]
        for i in range(1, len(values)):
            ema[i] = alpha * values[i] + (1 - alpha) * ema[i - 1]
        return ema

    def _set_signal(self, text: str, color: str):
        # ttk label color: use style OR fallback via tk.Label
        # easiest: swap to tk.Label-like coloring by setting foreground
        self.signal_label.config(text=text, foreground=color)

    # ---------- control ----------
    def set_symbol(self, symbol: str):
        self.symbol = symbol.upper()
        self.info.config(text=f"{self.symbol} | {self.interval} | last {self.limit}")

    def start(self):
        if self._active:
            return
        self._active = True
        self._schedule()

    def stop(self):
        self._active = False
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _schedule(self):
        if not self._active:
            return
        self._job = self.after(self.poll_ms, self._tick)
        self._tick()

    # ---------- main loop ----------
    def _tick(self):
        if not self._active:
            return

        try:
            self.status.config(text="Status: Updating...")
            klines = self.client.get_klines(self.symbol, self.interval, self.limit)

            close_prices = np.array([float(k[4]) for k in klines], dtype=float)

            # compute EMA
            ema_fast = self._ema(close_prices, self.ema_fast)
            ema_slow = self._ema(close_prices, self.ema_slow)

            # signal from crossover (use last 2 points)
            signal = "NEUTRAL"
            sig_color = "#9ca3af"

            if len(close_prices) >= 2:
                prev_fast, prev_slow = ema_fast[-2], ema_slow[-2]
                curr_fast, curr_slow = ema_fast[-1], ema_slow[-1]

                # crossover up
                if prev_fast <= prev_slow and curr_fast > curr_slow:
                    signal = "BUY (EMA Cross Up)"
                    sig_color = "#22c55e"
                # crossover down
                elif prev_fast >= prev_slow and curr_fast < curr_slow:
                    signal = "SELL (EMA Cross Down)"
                    sig_color = "#ef4444"
                else:
                    # trend bias
                    if curr_fast > curr_slow:
                        signal = "BULLISH"
                        sig_color = "#22c55e"
                    elif curr_fast < curr_slow:
                        signal = "BEARISH"
                        sig_color = "#ef4444"

            self._set_signal(f"Signal: {signal}", sig_color)

            # redraw
            self.ax.clear()

            # reapply dark style after clear()
            self.ax.set_facecolor("#111827")
            self.ax.tick_params(colors="#9ca3af")
            for spine in self.ax.spines.values():
                spine.set_visible(False)

            # plot lines
            self.ax.plot(close_prices, color="#3b82f6", linewidth=2, label="Close")
            self.ax.plot(ema_fast, color="#f59e0b", linewidth=1.6, label=f"EMA{self.ema_fast}")
            self.ax.plot(ema_slow, color="#a78bfa", linewidth=1.6, label=f"EMA{self.ema_slow}")

            self.ax.set_title(f"{self.symbol} Close Price ({self.interval})", color="#e5e7eb")
            self.ax.set_xlabel("Time Index", color="#9ca3af")
            self.ax.set_ylabel("Price", color="#9ca3af")
            self.ax.legend(loc="upper left", frameon=False, labelcolor="#e5e7eb")

            self.canvas.draw()
            self.status.config(text="Status: OK")

        except Exception:
            self.status.config(text="Status: Error (REST)")
            self._set_signal("Signal: --", "#9ca3af")
