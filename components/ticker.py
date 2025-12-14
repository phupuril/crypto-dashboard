import json
import threading
import tkinter as tk
from tkinter import ttk
import websocket

# ----- THEME -----
CARD_BG = "#111827"
TEXT_MAIN = "#e5e7eb"
TEXT_SUB = "#9ca3af"
GREEN = "#22c55e"
RED = "#ef4444"


class CryptoTickerPanel(tk.Frame):
    def __init__(self, parent, symbol, display_name, ws_base):
        super().__init__(parent, bg=CARD_BG, padx=16, pady=14)

        self.symbol = symbol.lower()
        self.display_name = display_name
        self.ws_base = ws_base
        self.ws = None
        self.active = False

        self.configure(highlightbackground="#1f2937", highlightthickness=1)

        # ---- UI ----
        tk.Label(
            self, text=display_name,
            fg=TEXT_SUB, bg=CARD_BG,
            font=("Arial", 11)
        ).pack(anchor="w")

        self.price_label = tk.Label(
            self, text="--",
            fg=TEXT_MAIN, bg=CARD_BG,
            font=("Arial", 26, "bold")
        )
        self.price_label.pack(anchor="w", pady=(6, 2))

        self.change_label = tk.Label(
            self, text="--",
            fg=TEXT_SUB, bg=CARD_BG,
            font=("Arial", 11)
        )
        self.change_label.pack(anchor="w")

        self.status = tk.Label(
            self, text="Disconnected",
            fg=TEXT_SUB, bg=CARD_BG,
            font=("Arial", 9)
        )
        self.status.pack(anchor="e", pady=(8, 0))

    # ----- WebSocket -----
    def start(self):
        if self.active:
            return
        self.active = True

        url = f"{self.ws_base}/{self.symbol}@ticker"
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

    def stop(self):
        self.active = False
        if self.ws:
            self.ws.close()

    def on_open(self, ws):
        self.after(0, lambda: self.status.config(text="Live"))

    def on_close(self, ws, *_):
        if self.winfo_exists():
            self.after(0, lambda: self.status.config(text="Disconnected"))

    def on_message(self, ws, message):
        if not self.active:
            return
        data = json.loads(message)

        price = float(data["c"])
        change = float(data["p"])
        percent = float(data["P"])

        self.after(0, self.update_ui, price, change, percent)

    def update_ui(self, price, change, percent):
        color = GREEN if change >= 0 else RED
        sign = "+" if change >= 0 else ""

        self.price_label.config(text=f"${price:,.2f}", fg=TEXT_MAIN)
        self.change_label.config(
            text=f"{sign}{change:,.2f} ({sign}{percent:.2f}%)",
            fg=color
        )
