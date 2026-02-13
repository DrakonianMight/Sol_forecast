# Deployment Comparison Guide

This repository is configured for easy deployment to both **Render** and **Streamlit Community Cloud** so you can compare their performance.

## Quick Summary

| Platform | Deployment Method | Cost | Expected Performance |
|----------|------------------|------|---------------------|
| **Render** | Docker | Free tier available | ~11.5s cold start, 2-5s warm |
| **Streamlit Community Cloud** | Git integration | Free | ~6-8s cold start, 1-3s warm |

---

## 🚀 Option 1: Streamlit Community Cloud (Recommended for Testing)

### Advantages
- ✅ **Free forever** (no credit card required)
- ✅ **Faster deployment** (~2 minutes)
- ✅ **Better performance** on free tier
- ✅ **No cold starts** (keeps apps warm longer)
- ✅ **Built specifically for Streamlit**
- ✅ **Auto-deploys on git push**

### Deployment Steps

1. **Go to Streamlit Community Cloud**
   - Visit: https://share.streamlit.io
   - Sign in with GitHub

2. **Deploy New App**
   - Click "New app"
   - Repository: `DrakonianMight/Sol_forecast`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - Click "Deploy"

3. **That's it!**
   - Your app will be live in ~2 minutes
   - URL format: `https://[app-name]-[username].streamlit.app`
   - Auto-redeploys on every push to main

### Configuration
No additional configuration needed! The app uses:
- ✅ `streamlit_app.py` (automatically detected)
- ✅ `requirements.txt` (automatically installed)
- ✅ `.streamlit/config.toml` (automatically loaded)

---

## 🐳 Option 2: Render (Docker Deployment)

### Advantages
- ✅ **Containerized** (more production-like)
- ✅ **More control** over environment
- ✅ **Can run non-Streamlit apps** (Flask, Dash, etc.)
- ✅ **Easier to upgrade** to paid tiers

### Deployment Steps

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Sign in with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect to `DrakonianMight/Sol_forecast` repository
   - Click "Connect"

3. **Configure Service**
   - **Name**: `weather-forecast-streamlit`
   - **Branch**: `main`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./docker/Dockerfile`
   - **Docker Context**: `./docker`
   - **Instance Type**: Free

4. **Environment Variables**
   Add these in the "Environment" section:
   ```
   CACHE_TTL=3600
   DEBUG_MODE=false
   PORT=8501
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for first build
   - Your app will be live at: `https://weather-forecast-streamlit.onrender.com`

### Using Render Blueprint (Faster)

Alternatively, use the included `render.yaml`:

```bash
# From repository root
git push origin main

# Render will auto-detect render.yaml and deploy
```

Or manually import:
1. In Render dashboard: "New +" → "Blueprint"
2. Connect to repository
3. Select `render.yaml`
4. Click "Apply"

---

## 📊 Performance Comparison

### Expected Results

#### Streamlit Community Cloud
- **Cold start**: 6-8 seconds
- **Warm load**: 1-3 seconds
- **Concurrent users**: 20-50
- **Uptime**: Very good (minimal cold starts)
- **Cache behavior**: Excellent

#### Render Free Tier
- **Cold start**: 10-15 seconds
- **Warm load**: 2-5 seconds
- **Concurrent users**: 10-30
- **Uptime**: Good (15min inactivity = cold start)
- **Cache behavior**: Good

#### Render Paid Tier ($7/month)
- **Cold start**: N/A (no cold starts)
- **Warm load**: 2-4 seconds
- **Concurrent users**: 50-100+
- **Uptime**: Excellent (always on)
- **Cache behavior**: Excellent

---

## 🧪 Testing Both Platforms

### Deploy to Both

1. **Deploy to Streamlit Community Cloud** (free, 5 min)
2. **Deploy to Render** (free tier, 10 min)
3. **Compare side-by-side**

### Metrics to Compare

| Metric | How to Measure |
|--------|---------------|
| **Load Time** | Time from URL open to fully rendered |
| **Cold Start** | After 15+ min inactivity |
| **Warm Load** | Immediate reload |
| **Interactions** | Time for chart updates |
| **Reliability** | Errors, timeouts, crashes |

### Testing Checklist

- [ ] Initial load time (cold start)
- [ ] Reload time (warm)
- [ ] Site selection responsiveness
- [ ] Map interaction
- [ ] Chart rendering
- [ ] Timezone changes
- [ ] Variable changes
- [ ] Ensemble forecast loading
- [ ] Observational data integration
- [ ] Multiple concurrent browsers

---

## 📁 File Structure

### For Streamlit Community Cloud
```
Sol_forecast/
├── streamlit_app.py        ← Main app (root level)
├── requirements.txt         ← Dependencies (root level)
├── siteList.csv            ← Data file (root level)
├── om_extract.py           ← API module (root level)
├── .streamlit/
│   └── config.toml         ← Streamlit config (root level)
└── docker/                 ← Render deployment files
    ├── app.py              ← Same as streamlit_app.py
    ├── Dockerfile
    ├── render.yaml
    └── ...
```

### For Render (Docker)
```
Sol_forecast/
└── docker/
    ├── app.py              ← Main app
    ├── om_extract.py       ← API module
    ├── siteList.csv        ← Data file
    ├── requirements.txt    ← Dependencies
    ├── Dockerfile          ← Docker config
    ├── render.yaml         ← Render blueprint
    └── .streamlit/
        └── config.toml     ← Streamlit config
```

**Note**: Files are duplicated (root + docker/) to support both platforms easily.

---

## 🔄 Updating Your App

### After Making Changes

**Streamlit Community Cloud**:
```bash
git add .
git commit -m "Update feature"
git push origin main
# Auto-deploys automatically!
```

**Render**:
```bash
git add .
git commit -m "Update feature"
git push origin main
# Render auto-detects and rebuilds (takes 5-10 min)
```

Both platforms auto-deploy on push to main branch!

---

## 💡 Recommendations

### For Your Situation

Based on your requirements (free tier, production-ready, good performance):

**Start with Streamlit Community Cloud** ✅
- Faster deployment
- Better free tier performance
- No cold start issues
- Easier to manage
- Perfect for your use case

**Use Render if**:
- You need Docker containerization
- You want to deploy multiple apps (Dash version)
- You plan to upgrade to paid tier
- You need more infrastructure control

### Best Approach
1. **Deploy to Streamlit Community Cloud first** (5 min setup)
2. **Test and share with users**
3. **If happy with performance**: Done! ✅
4. **If need more**: Deploy to Render and compare
5. **If Render better**: Upgrade to Starter ($7/month)

---

## 🆘 Troubleshooting

### Streamlit Community Cloud

**App not finding siteList.csv**
- ✅ Fixed! File is now in root directory
- Verify: `streamlit_app.py` and `siteList.csv` are in same directory

**Import errors (om_extract)**
- ✅ Fixed! `om_extract.py` copied to root
- Verify: `om_extract.py` exists in root

**App crashes on load**
- Check logs in Streamlit Cloud dashboard
- Look for missing dependencies in `requirements.txt`

### Render

**Build fails**
- Check Dockerfile path: `./docker/Dockerfile`
- Check Docker context: `./docker`
- Verify all files exist in `docker/` directory

**App times out**
- Increase build timeout in Render settings
- Check logs for errors

**Slow performance**
- Normal on free tier (cold starts)
- Upgrade to Starter ($7/month) for better performance

---

## 📊 Decision Matrix

| Factor | Streamlit Cloud | Render Free | Render Paid |
|--------|----------------|-------------|-------------|
| **Cost** | Free forever | Free | $7/month |
| **Setup time** | 2 min | 10 min | 10 min |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Cold starts** | Rare | Every 15min | None |
| **Uptime** | Excellent | Good | Excellent |
| **Ease of use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Flexibility** | Streamlit only | Any Docker | Any Docker |
| **Support** | Community | Good | Priority |

**Winner for your use case**: **Streamlit Community Cloud** 🏆

---

## 🚀 Next Steps

1. **Deploy to Streamlit Community Cloud** (recommended)
   - Fastest setup: 5 minutes
   - Best free tier performance
   - https://share.streamlit.io

2. **Test the app**
   - Load times
   - All features working
   - Share with a few users

3. **(Optional) Deploy to Render**
   - For comparison
   - If you want Docker deployment

4. **Compare and decide**
   - Which performs better for you?
   - Which is easier to manage?

---

## 📞 Support

- **Streamlit Cloud**: https://docs.streamlit.io/streamlit-community-cloud
- **Render**: https://render.com/docs
- **This repo issues**: https://github.com/DrakonianMight/Sol_forecast/issues

Good luck with your deployment! 🎉
