# 🚀 Antigena Defense System - Deployment Guide

## 📋 Overview
Deploy Antigena AI Defense System with:
- **Frontend**: Vercel (React + Vite)
- **Backend**: Render (FastAPI + Python)

---

## 🌐 Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (free)
- GitHub repository connected to Vercel

### Step 1: Connect Repository
1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Select the `ui` folder as root directory

### Step 2: Configure Build Settings
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install"
}
```

### Step 3: Environment Variables
Add these in Vercel dashboard:
- `VITE_API_URL`: Your Render backend URL (after backend deployment)

### Step 4: Deploy
- Click "Deploy"
- Vercel will automatically deploy on git push

---

## 🔧 Backend Deployment (Render)

### Prerequisites
- Render account (free tier available)
- GitHub repository connected to Render

### Step 1: Create New Service
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select repository root directory

### Step 2: Configure Service
```yaml
Name: antigena-backend
Runtime: Python 3.9
Build Command: pip install -r requirements.txt
Start Command: python antigena_defense/api/api.py
Health Check Path: /health
Port: 8000
```

### Step 3: Environment Variables
Add these in Render dashboard:
- `PYTHON_VERSION`: 3.9
- `PORT`: 8000
- `GOOGLE_AI_API_KEY`: (optional, for AI features)

### Step 4: Deploy
- Click "Create Web Service"
- Render will automatically deploy on git push

---

## 🔗 Post-Deployment Configuration

### 1. Update Frontend API URL
After backend deployment:
1. Get your Render URL (e.g., `https://antigena-backend.onrender.com`)
2. Go to Vercel dashboard
3. Add environment variable: `VITE_API_URL=https://your-render-url.com`
4. Redeploy frontend

### 2. CORS Configuration
The backend is already configured for CORS with:
- All localhost origins (for development)
- Your Vercel domain (update after deployment)

---

## 🧪 Testing Deployment

### 1. Health Checks
```bash
# Backend health
curl https://your-render-url.com/health

# Frontend access
# Open your Vercel URL in browser
```

### 2. API Testing
```bash
# Test chatbot endpoint
curl -X POST https://your-render-url.com/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "user_context": {}}'
```

### 3. Integration Testing
1. Open your Vercel-deployed frontend
2. Test the AI chatbot
3. Verify all dashboard features
4. Check responsive design

---

## 📊 Monitoring

### Vercel
- Real-time analytics
- Performance metrics
- Error tracking
- Deployment logs

### Render
- Service health monitoring
- Resource usage
- Build logs
- Performance metrics

---

## 🔧 Troubleshooting

### Common Issues

#### Frontend Issues
- **Build failures**: Check `package.json` and dependencies
- **API errors**: Verify `VITE_API_URL` environment variable
- **CORS errors**: Ensure backend allows your Vercel domain

#### Backend Issues
- **Import errors**: Check `requirements.txt` and Python version
- **Port conflicts**: Ensure PORT environment variable is set
- **Health check failures**: Verify `/health` endpoint exists

### Quick Fixes

1. **Frontend not loading**:
   ```bash
   # Check build locally
   cd ui && npm run build
   ```

2. **Backend API not responding**:
   ```bash
   # Check health endpoint
   curl http://localhost:8000/health
   ```

3. **CORS errors**:
   - Add your Vercel domain to backend CORS origins
   - Redeploy backend

---

## 📈 Scaling Considerations

### Frontend (Vercel)
- **Free tier**: 100GB bandwidth/month
- **Pro tier**: Unlimited bandwidth, custom domains
- **Edge functions**: For API calls if needed

### Backend (Render)
- **Free tier**: 750 hours/month, limited RAM
- **Starter tier**: $7/month, better performance
- **Production tier**: Custom scaling options

---

## 🔄 CI/CD Pipeline

### Automatic Deployments
Both platforms support automatic deployments:
- **Vercel**: Deploys on push to main branch
- **Render**: Deploys on push to main branch
- **Preview deployments**: Available for pull requests

### Manual Deployments
- **Vercel**: Trigger redeploy from dashboard
- **Render**: Trigger manual build from dashboard

---

## 📞 Support

### Documentation
- [Vercel Docs](https://vercel.com/docs)
- [Render Docs](https://render.com/docs)

### Common Issues
- Check deployment logs
- Verify environment variables
- Test locally first
- Monitor resource usage

---

## ✅ Deployment Checklist

- [ ] Frontend configured for Vercel
- [ ] Backend configured for Render
- [ ] Environment variables set
- [ ] CORS configured
- [ ] Health checks passing
- [ ] API endpoints tested
- [ ] Frontend-backend integration working
- [ ] Monitoring enabled
- [ ] Documentation updated

---

**🎉 Your Antigena AI Defense System is now production-ready!**
