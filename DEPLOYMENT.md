# 🚀 Deployment Guide - Smart Algo Trade

## 📋 Pre-Deployment Checklist

### Prerequisites
- [x] Node.js 18+ installed
- [x] Python 3.11+ installed
- [x] Docker & Docker Compose (optional, for containerized deployment)
- [x] Kite Connect API credentials
- [x] PostgreSQL or SQLite for production data storage (optional)

### Environment Setup
- [x] Configure `.env` in root directory
- [x] Configure `backend/.env` with API credentials
- [x] Review `backend/app/config.py` for production settings
- [x] Ensure `PAPER_TRADING=True` for testing

---

## 🏗️ Deployment Options

### Option 1: Traditional Deployment (Recommended for Development)

#### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd smart-algo-trade
```

#### 2. Configure Environment
```bash
# Frontend
cp .env.example .env
# Edit .env and set VITE_API_URL

# Backend
cp backend/.env.example backend/.env
# Edit backend/.env and add your Kite API credentials
```

#### 3. Build and Deploy
```bash
# Run the automated deployment script
chmod +x deploy.sh
./deploy.sh
```

#### 4. Start Services

**Backend:**
```bash
cd backend
./start_prod.sh  # Production mode
# or
./start_dev.sh   # Development mode with hot reload
```

**Frontend:**
```bash
# Development
npm run dev

# Production preview
npm run preview

# Or serve dist/ folder with nginx
```

---

### Option 2: Docker Deployment (Recommended for Production)

#### 1. Configure Environment
```bash
# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env

# Edit backend/.env with your API credentials
nano backend/.env
```

#### 2. Build and Start Containers
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### 3. Access Application
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔒 Security Considerations

### Production Checklist
- [ ] Change default CORS settings in `backend/main.py`
- [ ] Use HTTPS/SSL certificates
- [ ] Set strong SECRET_KEY for sessions
- [ ] Enable rate limiting
- [ ] Configure firewall rules
- [ ] Use environment variables for all secrets
- [ ] Never commit `.env` files
- [ ] Enable database backups
- [ ] Set up monitoring and alerts

### CORS Configuration
In `backend/main.py`, update CORS for production:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## 🌐 Production Server Setup

### Nginx Configuration (Recommended)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Frontend
    location / {
        root /var/www/smart-algo-trade/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### SSL/HTTPS Setup
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

---

## 📊 Monitoring & Logging

### Application Logs
```bash
# Backend logs
tail -f backend/logs/app.log

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health Checks
- Backend: http://localhost:8000/health
- Frontend: http://localhost/

### Performance Monitoring
Consider adding:
- Sentry for error tracking
- Prometheus + Grafana for metrics
- ELK stack for log aggregation

---

## 🔄 Updates & Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Update frontend
npm install
npm run build

# Update backend
cd backend
source ../venv/bin/activate
pip install -r requirements.txt

# Restart services
docker-compose restart  # If using Docker
# or restart systemd services
```

### Database Backups
```bash
# Backup session data
cp backend/data/kite_session.json backend/data/backups/

# Backup SQLite databases
cp backend/data/*.db backend/data/backups/
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in backend/.env
PORT=8001
```

**2. Authentication Issues**
- Verify Kite API credentials in `backend/.env`
- Check session expiry in `backend/data/kite_session.json`
- Re-login through the application

**3. WebSocket Connection Failed**
- Ensure backend is running
- Check CORS configuration
- Verify WebSocket proxy in nginx

**4. Frontend Build Errors**
```bash
# Clear cache and rebuild
rm -rf node_modules dist
npm install
npm run build
```

**5. Python Dependency Issues**
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

---

## 📈 Scaling Considerations

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Deploy multiple backend instances
- Use Redis for session management
- Implement message queue (RabbitMQ, Kafka)

### Database Optimization
- Migrate from SQLite to PostgreSQL/MySQL
- Add database indexes
- Implement connection pooling
- Set up read replicas

### Caching Strategy
- Implement Redis for market data caching
- Use CDN for static assets
- Enable browser caching

---

## 🎯 Performance Optimization

### Frontend Optimizations
- [x] Code splitting
- [x] Lazy loading
- [x] Asset compression
- [x] Tree shaking
- [ ] Service worker for offline support
- [ ] Progressive Web App (PWA)

### Backend Optimizations
- [x] FastAPI async operations
- [x] Connection pooling
- [x] Rate limiting
- [ ] Background task processing
- [ ] Caching layer

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- Daily: Monitor logs and errors
- Weekly: Check disk space and backups
- Monthly: Update dependencies and security patches
- Quarterly: Review and optimize database

### Emergency Response
1. Check application logs
2. Verify external API status (Kite Connect)
3. Check server resources (CPU, memory, disk)
4. Review recent deployments
5. Roll back if necessary

---

## 🎓 Additional Resources

- [Kite Connect Documentation](https://kite.trade/docs/connect/v3/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vite Documentation](https://vitejs.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

## ⚠️ Important Notes

### Paper Trading
- **ALWAYS test with `PAPER_TRADING=True` first**
- Verify all strategies in paper mode for at least 1 week
- Never deploy with live trading without thorough testing

### API Rate Limits
- Kite Connect has rate limits
- Implement exponential backoff
- Cache market data when possible

### Market Hours
- Application auto-adjusts based on market hours
- WebSocket connections may timeout outside market hours
- Plan maintenance during market close

---

## 📝 Deployment Log Template

```
Date: _______________
Version: _______________
Deployed By: _______________

Changes:
- 
- 
- 

Tests Performed:
- [ ] Authentication works
- [ ] Market data streaming
- [ ] Order placement (paper)
- [ ] WebSocket connections
- [ ] Historical data fetch
- [ ] Portfolio display

Issues:
- 

Rollback Plan:
- 
```

---

## ✅ Post-Deployment Verification

After deployment, verify:
1. [ ] Application loads successfully
2. [ ] Can login with Kite credentials
3. [ ] Market data is streaming
4. [ ] WebSocket connection is stable
5. [ ] Can place paper trades
6. [ ] Historical data fetching works
7. [ ] Portfolio displays correctly
8. [ ] No console errors
9. [ ] Mobile responsive design works
10. [ ] All API endpoints respond correctly

---

**Status**: ✅ Deployment Ready
**Last Updated**: December 31, 2025
**Version**: 2.0.0
