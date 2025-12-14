APP_TITLE = "Cryptocurrency Dashboard (Tkinter)"
APP_GEOMETRY = "1100x650"

# Assets required by rubric
DEFAULT_ASSETS = [
    ("BTCUSDT", "BTC/USDT"),
    ("ETHUSDT", "ETH/USDT"),
    ("SOLUSDT", "SOL/USDT"),
]

# Bonus assets (optional toggles)
EXTRA_ASSETS = [
    ("BNBUSDT", "BNB/USDT"),
    ("XRPUSDT", "XRP/USDT"),
]

REST_BASE = "https://api.binance.com"
WS_BASE = "wss://stream.binance.com:9443/ws"

# Polling intervals (ms)
ORDERBOOK_POLL_MS = 1500
TRADES_POLL_MS = 1500
CHART_POLL_MS = 10_000

# Chart settings
KLINE_INTERVAL = "1m"
KLINE_LIMIT = 60  # last 60 minutes

PREF_FILE = "preferences.json"
