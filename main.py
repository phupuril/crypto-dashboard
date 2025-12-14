import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# ==== your modules (keep names same as your project) ====
from utils.binance_api import BinanceRESTClient
from components.ticker import CryptoTickerPanel
from components.chart import CandleChartPanel

try:
    from components.orderbook import OrderBookPanel
except Exception:
    OrderBookPanel = None

try:
    from components.trades import RecentTradesPanel
except Exception:
    RecentTradesPanel = None


WS_BASE = "wss://stream.binance.com:9443/ws"
PREF_PATH = Path(__file__).with_name("preferences.json")


# =========================
# THEME PALETTES (mock-like)
# =========================
THEMES = {
    "light": {
        "APP_BG": "#eef2f7",
        "CARD_BG": "#ffffff",
        "CARD_INNER": "#ffffff",
        "BORDER": "#e5e7eb",
        "TEXT": "#111827",
        "SUBTEXT": "#6b7280",
        "BTN_BG": "#f3f4f6",
        "BTN_ACTIVE": "#e5e7eb",
        "BTN_TEXT": "#111827",
        "HEADER_BG": "#eef2f7",
        "ACCENT": "#2563eb",
    },
    "dark": {
        "APP_BG": "#0b1220",
        "CARD_BG": "#0f172a",
        "CARD_INNER": "#0f172a",
        "BORDER": "#1f2937",
        "TEXT": "#e5e7eb",
        "SUBTEXT": "#9ca3af",
        "BTN_BG": "#111827",
        "BTN_ACTIVE": "#1f2937",
        "BTN_TEXT": "#e5e7eb",
        "HEADER_BG": "#0b1220",
        "ACCENT": "#60a5fa",
    },
}


# =========================
# ttk styles
# =========================
def apply_style(root: tk.Tk, theme: dict):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # base
    style.configure("TFrame", background=theme["APP_BG"])
    style.configure("TLabel", background=theme["APP_BG"], foreground=theme["TEXT"], font=("Arial", 11))
    style.configure("Title.TLabel", background=theme["HEADER_BG"], foreground=theme["TEXT"], font=("Arial", 28, "bold"))
    style.configure("Sub.TLabel", background=theme["APP_BG"], foreground=theme["SUBTEXT"], font=("Arial", 11))

    # buttons
    style.configure(
        "TopBtn.TButton",
        font=("Arial", 11, "bold"),
        padding=(16, 10),
        background=theme["BTN_BG"],
        foreground=theme["BTN_TEXT"],
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "TopBtn.TButton",
        background=[("active", theme["BTN_ACTIVE"])],
        foreground=[("active", theme["BTN_TEXT"])],
    )

    style.configure(
        "MiniBtn.TButton",
        font=("Arial", 10, "bold"),
        padding=(14, 8),
        background=theme["BTN_BG"],
        foreground=theme["BTN_TEXT"],
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "MiniBtn.TButton",
        background=[("active", theme["BTN_ACTIVE"])],
        foreground=[("active", theme["BTN_TEXT"])],
    )

    # card text styles (harmless if not used by panels)
    style.configure("CardTitle.TLabel", background=theme["CARD_INNER"], foreground=theme["TEXT"], font=("Arial", 14, "bold"))
    style.configure("CardSub.TLabel", background=theme["CARD_INNER"], foreground=theme["SUBTEXT"], font=("Arial", 10))
    style.configure("CardHeader.TFrame", background=theme["CARD_INNER"])
    style.configure("CardBody.TFrame", background=theme["CARD_INNER"])


# =========================
# Rounded Card (Canvas)
# =========================
class RoundedCard(tk.Frame):
    """
    Real rounded corners using Canvas.
    - Does NOT destroy inner widgets on redraw
    - Supports fixed height (prevents layout jitter)
    """
    def __init__(self, parent, theme: dict, radius=18, padding=16, height=None):
        super().__init__(parent, bg=theme["APP_BG"])
        self.theme = theme
        self.radius = int(radius)
        self.padding = int(padding)
        self.fixed_height = height  # can be None

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=theme["APP_BG"])
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # inner container
        self.inner = tk.Frame(self.canvas, bg=theme["CARD_INNER"])
        self._win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")

        # keep size stable if height is given
        if self.fixed_height is not None:
            self.pack_propagate(False)
            self.configure(height=self.fixed_height)

        self.bind("<Configure>", self._redraw)

    def set_theme(self, theme: dict):
        self.theme = theme
        self.configure(bg=theme["APP_BG"])
        self.canvas.configure(bg=theme["APP_BG"])
        self.inner.configure(bg=theme["CARD_INNER"])
        self._redraw()

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        # points for smooth polygon
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _redraw(self, *_):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 2 or h <= 2:
            return

        self.canvas.delete("bg")

        # outer rounded card
        pad = 1
        r = min(self.radius, max(6, min(w, h) // 6))
        self._rounded_rect(
            pad, pad, w - pad, h - pad,
            r,
            fill=self.theme["CARD_BG"],
            outline=self.theme["BORDER"],
            width=1,
            tags="bg"
        )

        # inner area placement
        ip = self.padding
        self.canvas.coords(self._win, ip, ip)
        self.canvas.itemconfigure(self._win, width=w - (ip * 2), height=h - (ip * 2))


# =========================
# Dashboard App
# =========================
class DashboardApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Cryptocurrency Dashboard")
        self.root.geometry("1280x820")

        self.client = BinanceRESTClient()

        # state
        self.prefs = self._load_prefs()
        self.theme_name = self.prefs.get("theme", "light")
        self.theme = THEMES.get(self.theme_name, THEMES["light"])

        self.visible_assets = self.prefs.get("visible_assets", {
            "BTCUSDT": True, "ETHUSDT": True, "SOLUSDT": True, "BNBUSDT": True, "LTCUSDT": True
        })
        self.visible_panels = self.prefs.get("visible_panels", {
            "chart": True, "orderbook": True, "trades": True
        })
        self.current_symbol = self.prefs.get("current_symbol", "BTCUSDT")

        apply_style(self.root, self.theme)
        self.root.configure(bg=self.theme["APP_BG"])

        # holders
        self.ticker_cards = {}   # symbol -> card
        self.ticker_panels = {}  # symbol -> CryptoTickerPanel
        self.asset_btns = {}     # symbol -> button

        self._build_ui()
        self._apply_visibility_from_state()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # -------------------------
    # prefs
    # -------------------------
    def _load_prefs(self):
        try:
            if PREF_PATH.exists():
                with open(PREF_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_prefs(self):
        data = {
            "theme": self.theme_name,
            "visible_assets": self.visible_assets,
            "visible_panels": self.visible_panels,
            "current_symbol": self.current_symbol,
        }
        try:
            with open(PREF_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    # -------------------------
    # safe start/stop
    # -------------------------
    def _safe_start(self, obj):
        try:
            if obj is not None and hasattr(obj, "start"):
                obj.start()
        except Exception:
            pass

    def _safe_stop(self, obj):
        try:
            if obj is not None and hasattr(obj, "stop"):
                obj.stop()
        except Exception:
            pass

    # -------------------------
    # UI build (mock-like)
    # -------------------------
    def _build_ui(self):
        # wrapper with mock spacing
        self.wrapper = ttk.Frame(self.root, padding=(22, 18, 22, 18))
        self.wrapper.pack(fill=tk.BOTH, expand=True)

        self.wrapper.columnconfigure(0, weight=1)
        self.wrapper.rowconfigure(2, weight=1)

        # ===== Header row =====
        header = ttk.Frame(self.wrapper)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="Cryptocurrency Dashboard", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")

        header_btns = ttk.Frame(header)
        header_btns.grid(row=0, column=1, sticky="e")

        self.theme_btn = ttk.Button(
            header_btns,
            text="Dark Mode" if self.theme_name == "light" else "Light Mode",
            style="TopBtn.TButton",
            command=self.toggle_theme
        )
        self.theme_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.save_btn = ttk.Button(header_btns, text="Save PNG", style="TopBtn.TButton", command=self.save_png)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))

        # ===== Button row (assets left, panels right) =====
        btn_row = ttk.Frame(self.wrapper)
        btn_row.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        assets_bar = ttk.Frame(btn_row)
        assets_bar.grid(row=0, column=0, sticky="w")

        panels_bar = ttk.Frame(btn_row)
        panels_bar.grid(row=0, column=1, sticky="e")

        # asset toggles (mock-like)
        self.assets = [
            ("BTCUSDT", "BTC"),
            ("ETHUSDT", "ETH"),
            ("SOLUSDT", "SOL"),
            ("BNBUSDT", "BNB"),
            ("LTCUSDT", "LTC"),
        ]

        for sym, short in self.assets:
            b = ttk.Button(
                assets_bar,
                text=f"Hide {short}" if self.visible_assets.get(sym, True) else f"Show {short}",
                style="MiniBtn.TButton",
                command=lambda s=sym: self.toggle_asset(s)
            )
            b.pack(side=tk.LEFT, padx=(0, 10))
            self.asset_btns[sym] = b

        # panel toggles
        self.chart_btn = ttk.Button(
            panels_bar,
            text="Hide Chart" if self.visible_panels.get("chart", True) else "Show Chart",
            style="MiniBtn.TButton",
            command=lambda: self.toggle_panel("chart")
        )
        self.chart_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.ob_btn = ttk.Button(
            panels_bar,
            text="Hide Order Book" if self.visible_panels.get("orderbook", True) else "Show Order Book",
            style="MiniBtn.TButton",
            command=lambda: self.toggle_panel("orderbook")
        )
        self.ob_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.tr_btn = ttk.Button(
            panels_bar,
            text="Hide Trades" if self.visible_panels.get("trades", True) else "Show Trades",
            style="MiniBtn.TButton",
            command=lambda: self.toggle_panel("trades")
        )
        self.tr_btn.pack(side=tk.LEFT)

        # ===== Main grid (top tickers + bottom panels) =====
        main = ttk.Frame(self.wrapper)
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(2, weight=1)

        # --- top ticker area (two rows 3 + 2) ---
        top = ttk.Frame(main)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.columnconfigure(0, weight=1)

        row1 = ttk.Frame(top)
        row1.grid(row=0, column=0, sticky="ew")
        row1.columnconfigure((0, 1, 2), weight=1)

        row2 = ttk.Frame(top)
        row2.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        row2.columnconfigure((0, 1), weight=1)

        # fixed heights to look like mock and avoid jumping
        top_card_h = 126
        top_card_h2 = 126

        # create ticker cards
        placements = {
            "BTCUSDT": (row1, 0, (0, 14)),
            "ETHUSDT": (row1, 1, (0, 14)),
            "SOLUSDT": (row1, 2, (0, 0)),
            "BNBUSDT": (row2, 0, (0, 14)),
            "LTCUSDT": (row2, 1, (0, 0)),
        }

        for sym, short in self.assets:
            parent, col, padx = placements[sym]
            card = RoundedCard(parent, self.theme, radius=18, padding=14, height=top_card_h if parent is row1 else top_card_h2)
            card.grid(row=0, column=col, sticky="nsew", padx=padx)
            self.ticker_cards[sym] = card

            panel = CryptoTickerPanel(card.inner, sym, f"{short} / USDT", WS_BASE)
            panel.pack(fill=tk.BOTH, expand=True)
            self.ticker_panels[sym] = panel

        # start tickers that are visible
        for sym, _ in self.assets:
            if self.visible_assets.get(sym, True):
                self._safe_start(self.ticker_panels[sym])

        # --- bottom: left chart, right stack (orderbook + trades) ---
        bottom = ttk.Frame(main)
        bottom.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)
        bottom.rowconfigure(0, weight=1)

        # chart card
        self.chart_card = RoundedCard(bottom, self.theme, radius=18, padding=16)
        self.chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self._build_chart_area(self.chart_card.inner)

        # right column
        right = ttk.Frame(bottom)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # orderbook card
        self.ob_card = RoundedCard(right, self.theme, radius=18, padding=16)
        self.ob_card.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        self._build_orderbook_area(self.ob_card.inner)

        # trades card
        self.trades_card = RoundedCard(right, self.theme, radius=18, padding=16)
        self.trades_card.grid(row=1, column=0, sticky="nsew")
        self._build_trades_area(self.trades_card.inner)

        # start main panels
        self._safe_start(self.chart)
        if hasattr(self, "orderbook") and self.orderbook:
            self._safe_start(self.orderbook)
        if hasattr(self, "trades_panel") and self.trades_panel:
            self._safe_start(self.trades_panel)

    def _build_chart_area(self, parent):
        # Header line: title + asset selector (mock-like)
        header = ttk.Frame(parent, style="CardHeader.TFrame")
        header.pack(fill=tk.X)

        ttk.Label(header, text="Price Chart", style="CardTitle.TLabel").pack(side=tk.LEFT)

        # selector row
        sel = ttk.Frame(parent, style="CardHeader.TFrame")
        sel.pack(fill=tk.X, pady=(8, 8))

        ttk.Label(sel, text="Asset:", style="CardSub.TLabel").pack(side=tk.LEFT, padx=(0, 8))

        self.asset_var = tk.StringVar(value=self.current_symbol)
        self.asset_combo = ttk.Combobox(
            sel,
            textvariable=self.asset_var,
            values=[s for s, _ in self.assets],
            state="readonly",
            width=12
        )
        self.asset_combo.pack(side=tk.LEFT)
        self.asset_combo.bind("<<ComboboxSelected>>", lambda e: self.set_symbol(self.asset_var.get()))

        # actual chart panel (uses your CandleChartPanel)
        self.chart = CandleChartPanel(
            parent,
            client=self.client,
            symbol=self.current_symbol,
            interval="1m",
            limit=60,
            poll_ms=10_000
        )
        self.chart.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

    def _build_orderbook_area(self, parent):
        ttk.Label(parent, text="Order Book", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(parent, text="Order Book (Top 10)", style="CardSub.TLabel").pack(anchor="w", pady=(6, 8))

        if OrderBookPanel:
            self.orderbook = OrderBookPanel(parent, client=self.client, symbol=self.current_symbol, limit=10, poll_ms=3000)
            self.orderbook.pack(fill=tk.BOTH, expand=True)
        else:
            self.orderbook = None
            ttk.Label(parent, text="(OrderBookPanel not found)", style="CardSub.TLabel").pack(anchor="w")

    def _build_trades_area(self, parent):
        ttk.Label(parent, text="Recent Trades", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(parent, text="Live feed", style="CardSub.TLabel").pack(anchor="w", pady=(6, 8))

        if RecentTradesPanel:
            # IMPORTANT: keep ONE instance and only start/stop, do not recreate on toggle
            self.trades_panel = RecentTradesPanel(parent, self.current_symbol, WS_BASE, max_rows=12)
            self.trades_panel.pack(fill=tk.BOTH, expand=True)
        else:
            self.trades_panel = None
            ttk.Label(parent, text="(RecentTradesPanel not found)", style="CardSub.TLabel").pack(anchor="w")

    # -------------------------
    # apply visibility safely
    # -------------------------
    def _apply_visibility_from_state(self):
        # assets
        for sym, short in self.assets:
            show = self.visible_assets.get(sym, True)
            if show:
                self.ticker_cards[sym].grid()
                self.asset_btns[sym].configure(text=f"Hide {short}")
                self._safe_start(self.ticker_panels[sym])
            else:
                self._safe_stop(self.ticker_panels[sym])
                self.ticker_cards[sym].grid_remove()
                self.asset_btns[sym].configure(text=f"Show {short}")

        # panels
        for name in ("chart", "orderbook", "trades"):
            self._apply_panel_visibility(name)

    def _apply_panel_visibility(self, panel_name: str):
        vis = self.visible_panels.get(panel_name, True)

        if panel_name == "chart":
            if vis:
                self.chart_card.grid()
                self.chart_btn.configure(text="Hide Chart")
                self._safe_start(self.chart)
            else:
                self._safe_stop(self.chart)
                self.chart_card.grid_remove()
                self.chart_btn.configure(text="Show Chart")

        elif panel_name == "orderbook":
            if vis:
                self.ob_card.grid()
                self.ob_btn.configure(text="Hide Order Book")
                if hasattr(self, "orderbook") and self.orderbook:
                    self._safe_start(self.orderbook)
            else:
                if hasattr(self, "orderbook") and self.orderbook:
                    self._safe_stop(self.orderbook)
                self.ob_card.grid_remove()
                self.ob_btn.configure(text="Show Order Book")

        elif panel_name == "trades":
            if vis:
                self.trades_card.grid()
                self.tr_btn.configure(text="Hide Trades")
                if hasattr(self, "trades_panel") and self.trades_panel:
                    self._safe_start(self.trades_panel)
            else:
                if hasattr(self, "trades_panel") and self.trades_panel:
                    self._safe_stop(self.trades_panel)
                self.trades_card.grid_remove()
                self.tr_btn.configure(text="Show Trades")

    # -------------------------
    # actions
    # -------------------------
    def toggle_asset(self, symbol: str):
        # toggle state
        self.visible_assets[symbol] = not self.visible_assets.get(symbol, True)

        short = dict(self.assets)[symbol]
        if self.visible_assets[symbol]:
            self.ticker_cards[symbol].grid()
            self.asset_btns[symbol].configure(text=f"Hide {short}")
            self._safe_start(self.ticker_panels[symbol])
        else:
            self._safe_stop(self.ticker_panels[symbol])
            self.ticker_cards[symbol].grid_remove()
            self.asset_btns[symbol].configure(text=f"Show {short}")

        self._save_prefs()

    def toggle_panel(self, name: str):
        self.visible_panels[name] = not self.visible_panels.get(name, True)
        self._apply_panel_visibility(name)
        self._save_prefs()

    def set_symbol(self, symbol: str):
        """Change chart/orderbook/trades symbol together (mock UX)"""
        if symbol == self.current_symbol:
            return

        # stop dependent panels first (safe)
        self._safe_stop(self.chart)
        if hasattr(self, "orderbook") and self.orderbook:
            self._safe_stop(self.orderbook)
        if hasattr(self, "trades_panel") and self.trades_panel:
            self._safe_stop(self.trades_panel)

        self.current_symbol = symbol
        self.asset_var.set(symbol)

        # update chart panel (expects your CandleChartPanel to have set_symbol or symbol attr)
        if hasattr(self.chart, "set_symbol"):
            try:
                self.chart.set_symbol(symbol)
            except Exception:
                # fallback: recreate only chart safely (rare)
                pass
        else:
            # fallback: try attribute then restart
            try:
                setattr(self.chart, "symbol", symbol)
            except Exception:
                pass

        # update orderbook
        if hasattr(self, "orderbook") and self.orderbook:
            if hasattr(self.orderbook, "set_symbol"):
                try:
                    self.orderbook.set_symbol(symbol)
                except Exception:
                    pass
            else:
                try:
                    setattr(self.orderbook, "symbol", symbol)
                except Exception:
                    pass

        # update trades
        if hasattr(self, "trades_panel") and self.trades_panel:
            if hasattr(self.trades_panel, "set_symbol"):
                try:
                    self.trades_panel.set_symbol(symbol)
                except Exception:
                    pass
            else:
                # common signature: recreate trades panel safely inside card (only if needed)
                try:
                    # if panel supports direct symbol change, above handles
                    pass
                except Exception:
                    pass

        # restart only if visible
        if self.visible_panels.get("chart", True):
            self._safe_start(self.chart)
        if self.visible_panels.get("orderbook", True) and hasattr(self, "orderbook") and self.orderbook:
            self._safe_start(self.orderbook)
        if self.visible_panels.get("trades", True) and hasattr(self, "trades_panel") and self.trades_panel:
            self._safe_start(self.trades_panel)

        self._save_prefs()

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.theme = THEMES[self.theme_name]

        apply_style(self.root, self.theme)
        self.root.configure(bg=self.theme["APP_BG"])
        self.theme_btn.configure(text="Dark Mode" if self.theme_name == "light" else "Light Mode")

        # re-theme rounded cards
        for card in list(self.ticker_cards.values()) + [self.chart_card, self.ob_card, self.trades_card]:
            card.set_theme(self.theme)

        self._save_prefs()

    def save_png(self):
        """Save matplotlib chart as PNG"""
        try:
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")],
                title="Save chart as PNG"
            )
            if not path:
                return

            canvas = getattr(self.chart, "canvas", None)
            if canvas and hasattr(canvas, "figure"):
                canvas.figure.savefig(path, dpi=200, bbox_inches="tight")
                messagebox.showinfo("Saved", f"Saved PNG to:\n{path}")
                return

            if hasattr(self.chart, "fig"):
                self.chart.fig.savefig(path, dpi=200, bbox_inches="tight")
                messagebox.showinfo("Saved", f"Saved PNG to:\n{path}")
                return

            messagebox.showerror("Error", "Cannot find matplotlib Figure in chart panel.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_close(self):
        """Graceful shutdown (no crash, no noise)"""
        # stop tickers
        for sym, _ in self.assets:
            self._safe_stop(self.ticker_panels.get(sym))

        # stop panels
        self._safe_stop(getattr(self, "chart", None))
        self._safe_stop(getattr(self, "orderbook", None))
        self._safe_stop(getattr(self, "trades_panel", None))

        self._save_prefs()
        try:
            self.root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()
