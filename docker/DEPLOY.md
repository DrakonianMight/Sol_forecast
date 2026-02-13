# Deployment Guide - Weather Forecast Dashboard

## ✅ Pre-Deployment Checklist

Your app is now optimized and ready to deploy with:
- ✅ Performance tracking and logging
- ✅ Error handling throughout
- ✅ HTTP connection pooling
- ✅ Extended cache TTL (1 hour)
- ✅ Optimized Docker configuration
- ✅ Health checks
- ✅ Zero additional costs

## Quick Deploy to Render (Recommended)

### 1. Push to GitHub

```bash
cd /Users/lpeach/Documents/Python/repos/Sol_forecast/docker
git add .
git commit -m "Add production optimizations: logging, error handling, connection pooling"
git push origin main
```

### 2. Deploy on Render

1. Go to [render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `weather-forecast-app`
   - **Environment**: `Docker`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `docker`
   - **Plan**: Free (to start)

5. Add Environment Variables:
   ```
   CACHE_TTL=3600
   DEBUG_MODE=false
   ```

6. Click "Create Web Service"

### 3. Monitor Your Deployment

Once deployed, check the logs for:
- ✅ `🔧 Initializing HTTP session with connection pooling`
- ✅ `📍 Loading site data`
- ✅ `⏱️ Starting: [operation name]`
- ✅ `✅ [operation] completed in X.XXs`

## Deploy to Streamlit Community Cloud (Alternative)

1. Push code to GitHub (public repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your repository
5. Set:
   - **Main file path**: `docker/app.py`
   - **Python version**: 3.11
6. Click "Deploy"

## Environment Variables (Optional)

Set these in your deployment platform:

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_TTL` | `3600` | Cache duration in seconds (1 hour) |
| `DEBUG_MODE` | `false` | Show performance stats to users |

## Performance Monitoring

### View Logs on Render

1. Go to your service dashboard
2. Click "Logs" tab
3. Look for performance metrics:
   ```
   ⏱️ Starting: Fetch hourly data for Brisbane
   ✅ Fetch hourly data for Brisbane completed in 1.23s
   ✅ API call completed in 0.89s for 1 site(s)
   ```

### Enable Debug Mode (Temporarily)

Add to Render environment variables:
```
DEBUG_MODE=true
```

This will show performance stats in the sidebar for all users.

## Expected Performance (Free Tier)

- **First load**: 10-15s (cold start on free tier)
- **Cached load**: 1-3s
- **Concurrent users**: 20-30
- **Uptime**: Spins down after 15min inactivity

## Upgrade Path (When Needed)

### When you hit 50+ concurrent users:

1. **Upgrade to Render Starter** ($7/month)
   - No cold starts
   - Dedicated resources
   - 50-100 concurrent users

2. **Add Redis** ($10/month) - for distributed caching
   - Install on Render
   - Update code to use Redis (I can help)

## Troubleshooting

### Slow Performance
- Check logs for error patterns
- Verify cache TTL is set to 3600
- Look for repeated API calls (should be cached)

### Errors in Production
- Set `DEBUG_MODE=true` temporarily
- Check Render logs for stack traces
- Look for `❌` emoji in logs

### Cold Starts Too Slow
- Upgrade from Free to Starter plan ($7/month)
- Consider Streamlit Cloud (also free, but different limits)

## Health Check

Your app now includes a health check endpoint at:
```
https://your-app.onrender.com/_stcore/health
```

Render will automatically use this to monitor app health.

## Next Steps After Deployment

1. ✅ Share your URL with users
2. ✅ Monitor logs for errors
3. ✅ Track user feedback
4. ✅ Review performance metrics after 1 week

## Need More Scale?

When you consistently see 50+ users, contact me to implement:
- Redis distributed caching
- FastAPI backend
- Horizontal scaling

---

**Your app is production-ready! 🚀**
