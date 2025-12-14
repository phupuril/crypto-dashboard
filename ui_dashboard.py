import tkinter as tk
from tkinter import ttk

# ---------- THEME ----------
DARK_BG = "#0f172a"
CARD_BG = "#111827"
SIDEBAR_BG = "#020617"
TEXT_MAIN = "#e5e7eb"
TEXT_SUB = "#9ca3af"
ACCENT = "#2563eb"
GREEN = "#22c55e"
RED = "#ef4444"


class DashboardUI:
    def __init__(self, root):
        self.root = root
        root.title("Crypto Dashboard")
        root.geometry("1200x700")
        root.configure(bg=DARK_BG)

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        self.create_sidebar()
        self.create_main()

    # ---------- SIDEBAR ----------
    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg=SIDEBAR_BG, width=220)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        tk.Label(
            sidebar, text="Dashboard",
            fg=TEXT_MAIN, bg=SIDEBAR_BG,
            font=("Arial", 18, "bold")
        ).pack(pady=30)

        for item in ["Overview", "Chart", "Wallet", "News", "Settings"]:
            btn = tk.Label(
                sidebar, text=item,
                fg=TEXT_SUB, bg=SIDEBAR_BG,
                font=("Arial", 12)
            )
            btn.pack(anchor="w", padx=30, pady=10)

        tk.Label(
            sidebar, text="Logout",
            fg=TEXT_SUB, bg=SIDEBAR_BG
        ).pack(side="bottom", pady=20)

    # ---------- MAIN ----------
    def create_main(self):
        main = tk.Frame(self.root, bg=DARK_BG)
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(2, weight=1)

        self.create_cards(main)
        self.create_portfolio(main)
        self.create_chart(main)

    # ---------- CARDS ----------
    def create_cards(self, parent):
        cards = tk.Frame(parent, bg=DARK_BG)
        cards.grid(row=0, column=0, columnspan=2, sticky="ew")
        cards.grid_columnconfigure((0,1,2,3), weight=1)

        data = [
            ("Bitcoin", "$52,291", "+0.25%", GREEN),
            ("Ethereum", "$28,291", "+0.25%", GREEN),
            ("Solana", "$14,291", "-0.25%", RED),
            ("Litecoin", "$8,291", "+0.25%", GREEN),
        ]

        for i, (name, price, change, color) in enumerate(data):
            card = tk.Frame(cards, bg=CARD_BG, height=120)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            card.pack_propagate(False)

            tk.Label(card, text=name, fg=TEXT_SUB, bg=CARD_BG).pack(anchor="w", padx=15, pady=10)
            tk.Label(card, text=price, fg=TEXT_MAIN, bg=CARD_BG,
                     font=("Arial", 18, "bold")).pack(anchor="w", padx=15)
            tk.Label(card, text=change, fg=color, bg=CARD_BG).pack(anchor="w", padx=15)

    # ---------- PORTFOLIO ----------
    def create_portfolio(self, parent):
        portfolio = tk.Frame(parent, bg=CARD_BG)
        portfolio.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=10)

        tk.Label(
            portfolio, text="My Portfolio",
            fg=TEXT_MAIN, bg=CARD_BG,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=10)

        assets = [
            ("Bitcoin", "-6.00%", RED),
            ("Ethereum", "-3.40%", RED),
            ("Litecoin", "+14.25%", GREEN),
            ("Solana", "-2.00%", RED),
        ]

        for name, pct, color in assets:
            row = tk.Frame(portfolio, bg=CARD_BG)
            row.pack(fill="x", padx=15, pady=5)

            tk.Label(row, text=name, fg=TEXT_SUB, bg=CARD_BG).pack(side="left")
            tk.Label(row, text=pct, fg=color, bg=CARD_BG).pack(side="right")

    # ---------- CHART ----------
    def create_chart(self, parent):
        chart = tk.Frame(parent, bg=CARD_BG)
        chart.grid(row=1, column=1, rowspan=2, sticky="nsew", pady=10)

        tk.Label(
            chart, text="Chart",
            fg=TEXT_MAIN, bg=CARD_BG,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=10)

        # Placeholder (แทน matplotlib chart)
        canvas = tk.Canvas(chart, bg="#020617", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=15, pady=15)


if __name__ == "__main__":
    root = tk.Tk()
    DashboardUI(root)
    root.mainloop()
