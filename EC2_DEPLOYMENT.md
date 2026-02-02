# EC2 Deployment Guide

## Option 1: Same EC2 Instance (Docker Compose)

### Prerequisites
- EC2 instance with Docker and Docker Compose installed
- Port 80 (frontend) and 8001 (backend) open in security group
- At least 2GB RAM available

### Steps

1. **Clone the repository on EC2:**
```bash
cd /home/ec2-user
git clone <your-repo-url>
cd Trading-bot
```

2. **Build and Deploy with Docker Compose:**
```bash
docker-compose up -d
```

This will:
- Start frontend on port 80 (nginx)
- Start backend on port 8001
- Frontend will automatically proxy `/api/` requests to backend via nginx

3. **Access the application:**
```
http://<EC2-PUBLIC-IP>
```

### Verify it's working:
```bash
# Check if containers are running
docker-compose ps

# Check frontend logs
docker-compose logs frontend

# Check backend logs
docker-compose logs backend

# Test API endpoint
curl http://localhost:8001/api/analytics
```

---

## Option 2: Different EC2 Instances

### Setup

**Frontend EC2 Instance:**
1. Build frontend with backend URL:
```bash
docker build --build-arg REACT_APP_BACKEND_URL=http://<BACKEND-IP>:8001 -t trading-bot-frontend .
docker run -p 80:80 trading-bot-frontend
```

**Backend EC2 Instance:**
1. Start backend:
```bash
cd /path/to/backend
python -m pip install -r requirements.txt
python server.py
```

Or with Docker:
```bash
docker build -t trading-bot-backend .
docker run -p 8001:8001 trading-bot-backend
```

2. Update **frontend nginx.conf** to point to backend EC2:
```nginx
location /api/ {
    proxy_pass http://<BACKEND-EC2-IP>:8001/api/;
    # ... rest of config
}
```

---

## Option 3: Same Instance, Manual Services

### Frontend:
```bash
cd frontend
yarn install
REACT_APP_BACKEND_URL=http://localhost:8001 yarn build
# Serve with nginx or http-server
```

### Backend:
```bash
cd backend
pip install -r requirements.txt
python server.py --host 0.0.0.0 --port 8001
```

---

## Troubleshooting

### Frontend can't reach backend

**Issue:** "Failed to fetch analytics" error

**Solutions:**
1. Check backend is running: `curl http://<BACKEND-IP>:8001/api/analytics`
2. Check security group allows port 8001
3. Check REACT_APP_BACKEND_URL is set correctly
4. Check nginx proxy configuration

### Docker container issues

```bash
# Check if backend is accessible from frontend container
docker-compose exec frontend curl http://backend:8001/api/analytics

# Check backend logs
docker-compose logs backend --tail=50

# Restart services
docker-compose restart
```

### Port already in use

```bash
# Find process using port 80
netstat -tlnp | grep :80

# Kill process
kill -9 <PID>
```

---

## Environment Variables

Create a `.env.production` in frontend root:
```
REACT_APP_BACKEND_URL=http://your-backend-url:8001
```

When building Docker:
```bash
docker build --build-arg REACT_APP_BACKEND_URL=http://backend:8001 -f frontend/Dockerfile -t trading-bot-frontend .
```

---

## Health Checks

### Test Frontend
```bash
curl -I http://<EC2-IP>
# Should return 200 OK
```

### Test Backend
```bash
curl http://<EC2-IP>/api/summary
# Should return JSON with bot status
```

### Test Analytics Endpoint
```bash
curl http://<EC2-IP>/api/analytics
# Should return JSON with trading analytics
```

---

## CORS Issues

If you get CORS errors, the backend needs to allow the frontend origin. Update `backend/server.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## SSL/HTTPS (Optional but Recommended)

Use Let's Encrypt with nginx:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

Then update nginx.conf to use SSL.
