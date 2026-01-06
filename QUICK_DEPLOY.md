# 🚀 Quick Deployment Reference

## Instant Commands

### 🐳 Docker Deployment (Fastest)
```bash
# 1. Setup
cp .env.example .env
cp backend/.env.example backend/.env
nano backend/.env  # Add your Kite API credentials

# 2. Deploy
docker-compose up -d

# 3. Access
# Frontend: http://localhost
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 💻 Local Development
```bash
# Terminal 1 - Backend
cd backend
./start_dev.sh

# Terminal 2 - Frontend
npm run dev

# Access at http://localhost:3000
```

### 📦 Production Build
```bash
# Build
npm run build

# Start Backend
cd backend && ./start_prod.sh

# Preview Frontend
npm run preview
```

## Essential Environment Variables

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

### Backend (backend/.env)
```env
KITE_API_KEY=your_key_here
KITE_API_SECRET=your_secret_here
PAPER_TRADING=True
PORT=8000
WORKERS=2
```

## Troubleshooting

### Port in Use
```bash
lsof -ti:8000 | xargs kill -9
```

### Rebuild
```bash
rm -rf node_modules dist
npm install
npm run build
```

### Check Logs
```bash
# Docker
docker-compose logs -f

# Local
tail -f backend/logs/*.log
```

## Health Checks
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost/
```

## 📚 Full Documentation
- [README.md](./README.md) - Complete overview
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed guide
- [PRODUCTION_READY.md](./PRODUCTION_READY.md) - Status

**Status**: ✅ Ready for deployment
**Version**: 2.0.0
