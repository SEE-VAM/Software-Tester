# 🤖 AutoQA Robot - Automated POS Testing Engine

An autonomous UI crawler and test automation suite specifically engineered for retail POS (Point of Sale) systems like **BrainShop POS** as well as modern web applications.

---

## ⚡ Quick Start (1-Click Launch)

1. Simply double-click **`START_TESTER.bat`**.
2. If running for the first time, it will automatically install Playwright and Flask.
3. Your browser will immediately open the dashboard at:
   👉 **`http://localhost:9090`**

---

## 🎯 How to Test BrainShop POS

1. Make sure your BrainShop POS is running on `http://localhost:8080` (or your custom port).
2. On the **AutoQA Dashboard**:
   - Verify the **Target URL** is set to `http://localhost:8080`.
   - Toggle **"Visible Browser"** if you want to watch the robot click through the screen in real-time.
   - Click **`🚀 Start Auto-Test`**.
3. **What AutoQA will do automatically:**
   - Detects the login screen, enters default test credentials (`admin` / `password123`), and logs in.
   - Crawls through all sidebar modules (POS Terminal, Inventory, Held Orders, Khata, etc.).
   - Injects realistic synthetic test data (Product names, barcodes, prices, quantities, phone numbers).
   - Verifies buttons, modals, and input fields.
   - Catches unhandled JavaScript exceptions, dead clicks, and HTTP 4xx/5xx network errors.
   - Captures failure screenshots into `reports/screenshots/`.
4. Click **`📄 Export Report`** to generate a permanent standalone HTML audit report.

---

## 📁 Directory Structure

```
D:\Software tester\
│
├── crawler_engine.py          # Playwright autonomous DOM crawler & test engine
├── server.py                  # Flask REST & Server-Sent Events (SSE) telemetry server
├── requirements.txt           # Python dependencies (playwright, flask, requests)
├── START_TESTER.bat           # 1-Click Windows launcher
├── install_requirements.bat   # Dependency installer
├── README.md                  # Documentation and usage guide
│
├── web\                       # Modern Dark-Mode Dashboard Interface
│   ├── index.html             # Dashboard UI
│   ├── style.css              # Custom styling
│   └── app.js                 # Real-time SSE telemetry client
│
└── reports\                   # Generated HTML test audit reports
    └── screenshots\           # Failure screenshots and bug proof
```

---

## 🛠️ Requirements
- Python 3.10+ (Installed on system)
- Google Chrome or Playwright Chromium
