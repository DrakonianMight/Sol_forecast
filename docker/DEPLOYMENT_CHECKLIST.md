# Deployment Checklist - Optimized Free Tier

## ✅ Pre-Deployment

- [ ] All changes committed to git
- [ ] Tested locally with Docker
- [ ] Performance stats enabled (DEBUG_MODE=true for monitoring)
- [ ] Reviewed logs for errors
- [ ] Backup current deployment (if exists)

## 🚀 Deploy to Render

### 1. Push to GitHub
```bash
cd /Users/lpeach/Documents/Python/repos/Sol_forecast/docker
git add .
git commit -m "Add performance optimizations (no Redis)"
git push origin main
```

### 2. Configure Render Environment Variables

In Render Dashboard → Environment:

```bash
# Required
PORT=8501

# Performance optimization
CACHE_TTL=3600

# Monitoring (enable for first week)
DEBUG_MODE=true

# Optional: Disable after testing
# DEBUG_MODE=false
```

### 3. Deploy

- Go to Render Dashboard
- Click "Manual Deploy" → "Deploy latest commit"
- Wait 3-5 minutes for build

### 4. Verify Deployment

```bash
# Check health endpoint
curl https://your-app.onrender.com/_stcore/health

# Should return: {"status": "ok"}
```

## 📊 Post-Deployment Monitoring

### Day 1 - Launch Day

- [ ] Open app and test all features
- [ ] Check logs for errors: Render Dashboard → Logs
- [ ] Look for performance metrics in logs:
  ```
  ⏱️  Starting: Fetch hourly data
  ✅ Completed in X.XXs
  ```
- [ ] Test with multiple browsers/devices
- [ ] Verify maps load correctly
- [ ] Test both Deterministic and Ensemble forecasts

### Week 1 - Performance Baseline

Monitor daily in Render Dashboard:

**Metrics to Track:**
- [ ] Average response time (should be <5s after warmup)
- [ ] Error rate (should be <1%)
- [ ] Cold start frequency (how often container spins down)
- [ ] Memory usage (should stay <512MB)

**Check Logs For:**
```bash
# Good signs
✅ Cache HIT                    # Cache is working
✅ API call completed in 1.2s   # Good API performance
✅ Page loaded in 3.5s          # Good overall performance

# Warning signs
⚠️  Cache MISS                  # Normal on first load
⚠️  API call completed in 10s+  # API might be slow
❌ Error retrieving data        # API or code issue
```

### Week 2-4 - Optimization Period

Based on Week 1 metrics, decide:

#### If Performance is GOOD (5s loads, <1% errors):
✅ **Stay on free tier**
- [ ] Disable DEBUG_MODE: `DEBUG_MODE=false`
- [ ] Document baseline metrics
- [ ] Set up weekly monitoring schedule

#### If Performance is MARGINAL (10s loads, 1-5% errors):
⚠️ **Consider optimization**
- [ ] Review logs for bottlenecks
- [ ] Check if specific API calls are slow
- [ ] Consider Render Starter ($7/month)

#### If Performance is POOR (20s+ loads, >5% errors):
❌ **Upgrade needed**
- [ ] Upgrade to Render Starter ($7/month)
- [ ] Consider adding Redis ($10/month)
- [ ] Review architecture options

## 🔍 Troubleshooting

### Issue: Slow First Load (60s+)
**Cause**: Cold start on free tier
**Solutions**:
1. Accept it (free tier limitation)
2. Upgrade to Render Starter ($7/month)
3. Use a ping service to keep warm (see below)

### Issue: API Errors
**Cause**: Open-Meteo API rate limits or downtime
**Solutions**:
1. Check logs for specific errors
2. Verify Open-Meteo API status
3. Errors should be caught gracefully now

### Issue: Out of Memory
**Cause**: Too many cached items or concurrent users
**Solutions**:
1. Reduce CACHE_TTL: `CACHE_TTL=1800`
2. Upgrade to Starter plan (more memory)
3. Monitor memory in Render Dashboard

### Issue: High Error Rate
**Cause**: Code bugs or external API issues
**Solutions**:
1. Check logs for error patterns
2. Test locally with same parameters
3. Report issues to Open-Meteo if API problem

## 💡 Free Tier Optimization Tips

### Keep Container Warm (Free Method)
Use UptimeRobot or similar (free tier):
1. Sign up at uptimerobot.com
2. Create HTTP monitor for your app URL
3. Set check interval to 5 minutes
4. This pings your app every 5 min, keeping it warm

**Pros**: No cold starts during business hours
**Cons**: Uses some of your 750 hour/month allowance

### Monitor with Google Analytics (Free)
Add to `app.py` for user analytics:
```python
# After st.set_page_config()
st.markdown("""
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=YOUR-GA-ID"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'YOUR-GA-ID');
    </script>
""", unsafe_allow_html=True)
```

### Alternative: Streamlit Community Cloud
If Render free tier proves insufficient:
1. Push to GitHub (public repo)
2. Connect at share.streamlit.io
3. Completely free
4. Better performance than Render free
5. No credit card required

## 📈 Success Metrics

After 1 month, you should see:

### Performance
- ✅ Cached loads: 1-3 seconds
- ✅ Fresh loads: 5-8 seconds
- ✅ Error rate: <1%
- ✅ 20-30 concurrent users (free tier)

### Cost
- ✅ $0/month (free tier)
- ✅ If needed: $7/month (Starter)
- ✅ If needed: $17/month (Starter + Redis)

### User Experience
- ✅ Fast, responsive interface
- ✅ Graceful error handling
- ✅ Reliable data fetching
- ✅ Works on mobile

## 🎯 Decision Matrix

After 1 month of monitoring:

| Users | Load Time | Errors | Recommendation | Cost |
|-------|-----------|--------|----------------|------|
| <20 | <5s | <1% | ✅ Stay on free tier | $0 |
| 20-50 | 5-10s | 1-3% | ⚠️ Consider Starter | $7/mo |
| 50-100 | 10-15s | 3-5% | 🔄 Upgrade Starter + Redis | $17/mo |
| 100+ | >15s | >5% | 🚀 FastAPI backend | $24/mo |

## 📞 Support

If you encounter issues:

1. **Check logs first**: Render Dashboard → Logs
2. **Review this checklist**: Most issues covered here
3. **Test locally**: Docker image should work identically
4. **GitHub Issues**: Document bugs with logs

---

## 🎉 You're Ready!

The optimizations are in place. Time to deploy and monitor. Remember:
- Start on free tier
- Monitor for 1-4 weeks
- Upgrade only if metrics show need
- These optimizations should keep you on free tier for 20-30 users

Good luck! 🚀
