import tkinter as tk
from tkinter import ttk
from typing import Optional

from utils.binance_api import BinanceRESTClient


class OrderBookPanel(ttk.Frame):
    """
    Order book panel (top bids/asks) via REST polling.
    Uses Tkinter after() timer (event-driven).
    """

    def __init__(self, parent, client: BinanceRESTClient, symbol: str, poll_ms: int = 1500, limit: int = 10):
        super().__init__(parent, padding=12)
        self.client = client
        self.symbol = symbol.upper()
        self.poll_ms = poll_ms
        self.limit = limit

        self._job: Optional[str] = None
        self._active = False

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Order Book (Top 10)", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        self.sym_label = ttk.Label(top, text=f"Symbol: {self.symbol}", font=("Arial", 10))
        self.sym_label.pack(side=tk.RIGHT)

        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Two tables: bids and asks
        bids_frame = ttk.Frame(body)
        asks_frame = ttk.Frame(body)
        bids_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        asks_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        ttk.Label(bids_frame, text="BIDS", font=("Arial", 11, "bold")).pack(anchor="w")
        ttk.Label(asks_frame, text="ASKS", font=("Arial", 11, "bold")).pack(anchor="w")

        self.bids = tk.Text(bids_frame, height=18, width=45)
        self.asks = tk.Text(asks_frame, height=18, width=45)
        self.bids.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.asks.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.status = ttk.Label(self, text="Status: Idle", font=("Arial", 9))
        self.status.pack(anchor="w", pady=(8, 0))

        # Make text read-only style
        self.bids.config(state="disabled")
        self.asks.config(state="disabled")

    def set_symbol(self, symbol: str):
        self.symbol = symbol.upper()
        self.sym_label.config(text=f"Symbol: {self.symbol}")

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
        # do first update immediately
        self._tick()

    def _tick(self):
        if not self._active:
            return
        try:
            self.status.config(text="Status: Updating...")
            ob = self.client.get_orderbook(self.symbol, limit=self.limit)
            bids = ob.get("bids", [])[: self.limit]
            asks = ob.get("asks", [])[: self.limit]

            bids_text = "Price\t\tQty\n" + "\n".join([f"{float(p):,.2f}\t{float(q):,.6f}" for p, q in bids])
            asks_text = "Price\t\tQty\n" + "\n".join([f"{float(p):,.2f}\t{float(q):,.6f}" for p, q in asks])

            self._set_text(self.bids, bids_text)
            self._set_text(self.asks, asks_text)
            self.status.config(text="Status: OK")
        except Exception as e:
            self.status.config(text="Status: Error (REST)")

    @staticmethod
    def _set_text(widget: tk.Text, text: str):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.config(state="disabled")
