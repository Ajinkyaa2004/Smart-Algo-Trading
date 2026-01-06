# 🎯 Smart Algo Trade - Production Ready

A professional algorithmic trading platform built with React, TypeScript, FastAPI, and Kite Connect API.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-success.svg)

---

## ✨ Features

### Trading Features
- 🔐 **Secure Authentication** - Kite Connect OAuth integration
- 📊 **Real-time Market Data** - Live streaming with WebSocket
- 📈 **Historical Data** - Comprehensive historical analysis
- 🤖 **Automated Trading Bot** - Strategy-based execution
- 📝 **Paper Trading** - Risk-free strategy testing
- 💼 **Portfolio Management** - Real-time P&L tracking
- 📉 **Technical Indicators** - RSI, MACD, Bollinger Bands, and more
- 🎯 **Multiple Strategies** - Price action, indicators, and patterns

### Technical Features
- ⚡ **Fast & Responsive** - Built with React & Vite
- 🎨 **Modern UI** - Tailwind CSS with dark theme
- 📱 **Mobile Friendly** - Responsive design
- 🔄 **Real-time Updates** - WebSocket integration
- 🐳 **Docker Ready** - Containerized deployment
- 🔒 **Secure** - Environment-based configuration
- 📦 **Optimized Build** - Code splitting & lazy loading
- 🚀 **Production Ready** - Comprehensive deployment guide

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Kite Connect API credentials

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd smart-algo-trade
```

2. **Setup environment**
```bash
# Frontend
cp .env.example .env

# Backend
cp backend/.env.example backend/.env
# Edit backend/.env and add your Kite API credentials
```

3. **Install dependencies**
```bash
# Frontend
npm install

# Backend
python3 -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
```

4. **Run development servers**

**Terminal 1 - Backend:**
```bash
cd backend
./start_dev.sh
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🐳 Docker Deployment

### Quick Start with Docker
```bash
# Configure environment
cp .env.example .env
cp backend/.env.example backend/.env

# Edit backend/.env with your credentials
nano backend/.env

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 📁 Project Structure

```
smart-algo-trade/
├── src/                      # Frontend React application
│   ├── components/          # Reusable UI components
│   ├── pages/              # Page components
│   ├── layout/             # Layout components
│   └── lib/                # Utilities
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── services/      # Business logic
│   │   └── strategies/    # Trading strategies
│   ├── data/              # Data storage
│   └── main.py            # Application entry
├── docs/                   # Documentation
├── docker-compose.yml      # Docker configuration
├── deploy.sh              # Deployment script
└── DEPLOYMENT.md          # Detailed deployment guide
```

---

## 🔧 Configuration

### Frontend Configuration (.env)
```env
VITE_API_URL=http://localhost:8000
```

### Backend Configuration (backend/.env)
```env
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
PAPER_TRADING=True
MAX_LOSS_PER_DAY=5000.0
MAX_POSITIONS=3
HOST=0.0.0.0
PORT=8000
WORKERS=2
```

---

## 📚 Scripts

### Frontend
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run build:prod   # Build with production optimizations
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### Backend
```bash
./start_dev.sh       # Start development server (hot reload)
./start_prod.sh      # Start production server
```

### Deployment
```bash
./deploy.sh          # Automated deployment setup
```

---

## 🛡️ Security

- ✅ Environment variables for secrets
- ✅ CORS configuration
- ✅ Input validation
- ✅ Rate limiting ready
- ✅ HTTPS support (via nginx)
- ✅ Paper trading mode by default
- ✅ Session management

**⚠️ IMPORTANT:** Always test with `PAPER_TRADING=True` before live trading!

---

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - Kite Connect login
- `POST /api/auth/callback` - OAuth callback
- `GET /api/auth/status` - Check auth status

### Market Data
- `GET /api/market/quote` - Get stock quotes
- `GET /api/market/historical` - Historical data
- `GET /api/market/instruments` - Available instruments

### Orders
- `POST /api/orders/place` - Place order
- `GET /api/orders/list` - Get all orders
- `DELETE /api/orders/{order_id}` - Cancel order

### Portfolio
- `GET /api/portfolio/positions` - Current positions
- `GET /api/portfolio/holdings` - Holdings
- `GET /api/portfolio/pnl` - P&L summary

### Live Data
- `WS /ws` - WebSocket for live data
- `POST /api/live/subscribe` - Subscribe to symbols
- `POST /api/live/unsubscribe` - Unsubscribe

### Paper Trading
- `POST /api/paper-trading/order` - Place paper order
- `GET /api/paper-trading/positions` - Paper positions
- `POST /api/paper-trading/reset` - Reset paper account

Full API documentation: http://localhost:8000/docs

---

## 🐛 Troubleshooting

Common issues and solutions are documented in [DEPLOYMENT.md](./DEPLOYMENT.md#troubleshooting).

### Quick Fixes

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Authentication issues:**
- Check Kite API credentials
- Verify session in `backend/data/kite_session.json`
- Re-login through application

**Build errors:**
```bash
rm -rf node_modules dist
npm install
npm run build
```

---

## 📖 Documentation

- [Deployment Guide](./DEPLOYMENT.md) - Complete deployment instructions
- [Quick Start Guide](./docs/QUICK_START.md) - Get started quickly
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Trading Bot Guide](./docs/TRADING_BOT_GUIDE.md) - Bot usage guide
- [Paper Trading Guide](./docs/PAPER_TRADING_GUIDE.md) - Paper trading setup

---

## ⚠️ Disclaimer

This software is for educational purposes only. Trading in financial markets carries risk. Always:

- Test thoroughly with paper trading first
- Understand the risks involved
- Never trade with money you can't afford to lose
- Comply with local regulations
- Use proper risk management

The authors and contributors are not responsible for any financial losses incurred through the use of this software.

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- [Kite Connect](https://kite.trade/) - Trading API
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend library
- [Vite](https://vitejs.dev/) - Build tool
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework

---

## 📈 Status

**Current Version:** 2.0.0  
**Status:** ✅ Production Ready  
**Last Updated:** December 31, 2025

---

**Made with ❤️ for algorithmic traders**
# Smart-Algo-Trading
# Smart-Algo-Trading
