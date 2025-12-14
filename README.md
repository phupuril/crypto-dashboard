# Cryptocurrency Dashboard

## Student Information
- **Name:** Puril Injun  
- **Student ID:** 6810545875  
- **Program:** Software and Knowledge Engineering  
- **University:** Kasetsart University  

---

## Project Description
This project is a **Cryptocurrency Dashboard Application** developed as part of a university course.  
The application provides real-time cryptocurrency market data using the Binance API, including live prices, technical indicators, order book data, and recent trades.

The system is designed with a clean object-oriented architecture and an interactive graphical user interface using **Tkinter** and **Matplotlib**.

---

## Features

### Core Features
- Real-time cryptocurrency price updates via WebSocket
- Supports multiple cryptocurrencies (BTC, ETH, SOL, BNB, LTC)
- Color-coded price changes (green/red)
- Displays 24-hour price change and percentage
- Graceful shutdown with proper resource cleanup

### Advanced Features
- Candlestick chart with EMA indicators (EMA12, EMA26)
- Order Book (Top 10 Bids & Asks)
- Recent Trades feed (live updates)
- Asset selection for chart visualization
- Light / Dark mode toggle
- Individual toggle buttons for each asset and panel
- Responsive and organized UI layout

---

## Technologies Used
- Python 3
- Tkinter (GUI)
- Matplotlib (Chart Visualization)
- Binance API (REST & WebSocket)
- Object-Oriented Programming (OOP)

---

## How to Run the Application

### 1. Install Python
Ensure **Python 3.10 or higher** is installed.

### 2. Install dependencies
```bash
pip install -r requirements.txt
