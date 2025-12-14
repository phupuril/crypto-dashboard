import json
import threading
from collections import deque
from datetime import datetime
import tkinter as tk
from tkinter import ttk

try:
    import websocket  # websocket-client
except Exception:
    websocket = None


class RecentTradesPanel(tk.Frame):
    """
    Recent Trades Panel (Binance WebSocket)
    Layout + Style ให้เหมือน UI mockup
    """

    def __init__(self, parent, symbol="BTCUSDT",
                 ws_base="wss://stream.binance.com:9443/ws",
                 max_rows=10):
        super().__init__(parent, bg="#ffffff")

        self.symbol = symbol.upper()
        self.ws_base = ws_base
        self.max_rows = max_rows

        self._ws = None
        self._thread = None
        self._running = False
        self._rows = deque(maxlen=max_rows)

        # =====================
        # Header
        # =====================
        header = tk.Frame(self, bg="#ffffff")
        header.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            header,
            text="Recent Trades",
            bg="#ffffff",
            fg="#111827",
            font=("Arial", 13, "bold")
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text=f"Symbol: {self.symbol}",
            bg="#ffffff",
            fg="#6b7280",
            font=("Arial", 10)
        ).pack(side=tk.RIGHT)

        # =====================
        # Table
        # =====================
        style = ttk.Style()
        style.configure(
            "Trades.Treeview",
            font=("Arial", 10),
            rowheight=26
        )
        style.configure(
            "Trades.Treeview.Heading",
            font=("Arial", 10, "bold")
        )

        self.tree = ttk.Treeview(
            self,
            columns=("time", "side", "price"),
            show="headings",
            height=max_rows,
            style="Trades.Treeview"
        )

        self.tree.heading("time", text="Time")
        self.tree.heading("side", text="Side")
        self.tree.heading("price", text="Price")

        self.tree.column("time", width=90, anchor="w")
        self.tree.column("side", width=70, anchor="center")
        self.tree.column("price", width=120, anchor="e")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # สี BUY / SELL
        self.tree.tag_configure("BUY", foreground="#16a34a")
        self.tree.tag_configure("SELL", foreground="#dc2626")

        # Status
        self.status = tk.Label(
            self,
            text="Status: Idle",
            bg="#ffffff",
            fg="#6b7280",
            font=("Arial", 9)
        )
        self.status.pack(anchor="w", pady=(4, 0))

        if websocket is None:
            self.status.config(text="Status: websocket-client not installed")

    # =====================
    # WebSocket
    # =====================
    def start(self):
        if websocket is None or self._running:
            return

        self._running = True
        self.status.config(text="Status: Live")

        stream = f"{self.symbol.lower()}@trade"
        url = f"{self.ws_base}/{stream}"

        def on_message(ws, message):
            try:
                data = json.loads(message)

                price = float(data["p"])
                trade_time = datetime.fromtimestamp(
                    data["T"] / 1000
                ).strftime("%H:%M:%S")

                side = "SELL" if data["m"] else "BUY"

                self._rows.appendleft(
                    (trade_time, side, f"{price:,.2f}")
                )

                self.after(0, self._render)

            except Exception:
                pass

        def run():
            self._ws = websocket.WebSocketApp(
                url,
                on_message=on_message
            )
            self._ws.run_forever(ping_interval=20)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        try:
            if self._ws:
                self._ws.close()
        except Exception:
            pass
        self.status.config(text="Status: Idle")

    # =====================
    # Render Table
    # =====================
    def _render(self):
        self.tree.delete(*self.tree.get_children())

        for time_, side, price in list(self._rows):
            self.tree.insert(
                "",
                "end",
                values=(time_, side, price),
                tags=(side,)
            )
