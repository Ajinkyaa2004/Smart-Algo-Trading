# 🚀 Smart Algo Trade - Startup Guide

Follow these steps to run the complete trading system (Backend + Frontend).

## 1. Prerequisites
Ensure you have the following installed:
- Python 3.9+
- Node.js & npm
- Git

## 2. Start the Backend Server (Term 1)
Open a new terminal window at the project root and run:

```bash
# Create Virtual Environment (One time setup)
python -m venv venv

# Activate Virtual Environment
# For Mac/Linux:
source venv/bin/activate
# For Windows:
# .\venv\Scripts\activate

# Install Dependencies (If not already installed)
pip install -r backend/requirements.txt

# Run the FastAPI Server
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> **Success:** You should see `Application startup complete` and server running at `http://localhost:8000`.

## 3. Start the Frontend Application (Term 2)
Open a **new** terminal window (keep the backend running) and run:

```bash
# Navigate to project root (if not already there)
# cd /path/to/smart-algo-trade

# Install Node Modules (If not already installed)
npm install

# Start the Vite Development Server (Port 3000)
npm run dev
```

> **Success:** You should see `Local: http://localhost:3000/`.

## 4. Access the Application
1. Open your browser and go to: **[http://localhost:3000](http://localhost:3000)**
2. You will be redirected to the **Login Page**.
3. Click **"Login with Kite"** to authenticate with Zerodha.
4. Once logged in, you will see the **Dashboard** and **Live Market Data**.

## 🔄 Common Commands
| Action | Command |
|_ | _ |
| **Stop Server** | Press `Ctrl + C` in the terminal |
| **Check Backend API** | Visit `http://localhost:8000/docs` |
| **Check Live Status** | Visit `http://localhost:8000/api/live/status` |

## ⚠️ Troubleshooting
- **Port 3000/8000 In Use:** 
  - Run `kill $(lsof -t -i:3000)` or `kill $(lsof -t -i:8000)` to free ports.
- **Login Error:** 
  - Ensure your `.env` file has the correct `KITE_API_KEY` and `KITE_API_SECRET`.
  - Ensure your Zerodha Redirect URL is set to `http://localhost:8000/api/auth/callback`.

---
**Happy Trading! 📈**
