# 🚀 Deploy to Railway - Step by Step Guide

## 📋 Pre-Deployment Checklist (✅ Ready!)

Your project is already configured for Railway deployment:
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Railway start command  
- ✅ `railway.json` - Railway configuration
- ✅ Bible data and app code ready
- ✅ Git repository initialized

## 🚀 Deployment Steps

### Step 1: Commit All Changes
```bash
# Add all files to git
git add .

# Commit changes
git commit -m "Prepare for Railway deployment - added config files"

# Push to GitHub (make sure you have a GitHub repo)
git push origin main
```

### Step 2: Deploy to Railway
1. **Go to Railway**: [railway.app](https://railway.app)
2. **Sign up/Login** with GitHub account
3. **Create New Project** → "Deploy from GitHub repo"
4. **Select Repository**: Choose your `verse-checker` repo
5. **Deploy**: Railway will automatically:
   - Detect Python app
   - Install dependencies from `requirements.txt`
   - Load Bible data
   - Start the API server
   - Give you a live URL

### Step 3: Configure Environment (Optional)
After deployment, you can set environment variables:
- Go to your project in Railway
- Click "Variables" tab
- Add any needed environment variables:
  ```
  LOG_LEVEL=INFO
  SIMILARITY_THRESHOLD=0.7
  ```

### Step 4: Test Your Live API
```bash
# Replace YOUR_APP_URL with your actual Railway URL
export API_URL="https://your-app-name.railway.app"

# Test health check
curl $API_URL/health

# Test verse checking
curl -X POST $API_URL/check \
     -H "Content-Type: application/json" \
     -d '{"quote": "For God so loved the world"}'

# View API documentation
open $API_URL/docs
```

## 🎯 Expected Timeline
- **Commit & Push**: 1 minute
- **Railway Setup**: 2 minutes  
- **Deployment**: 2-3 minutes
- **Testing**: 1 minute
- **Total**: ~5-7 minutes

## 🔍 Troubleshooting

### If deployment fails:
1. Check Railway deployment logs
2. Ensure all files are committed and pushed
3. Verify `requirements.txt` has all dependencies

### If API doesn't respond:
1. Check Railway logs for startup errors
2. Ensure Railway assigned a port (should be automatic)
3. Wait 2-3 minutes for initial model download

## 🎉 Success Indicators
- ✅ Railway shows "Deployed" status
- ✅ Health check returns `{"status": "healthy"}`
- ✅ API docs accessible at `/docs`
- ✅ Verse checking works with test quote

## 📱 Sharing Your API
Once deployed, you can share:
- **API URL**: `https://your-app-name.railway.app`
- **Documentation**: `https://your-app-name.railway.app/docs`
- **Health Check**: `https://your-app-name.railway.app/health`

Ready to deploy? Let's go! 🚀