# Render Deployment Guide

## Quick Deployment Steps

### Option 1: Using render.yaml (Recommended)

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository with your app
   - Render will automatically detect the `render.yaml` file
   - Click "Apply" to deploy

### Option 2: Manual Setup

1. **Push your code to GitHub**

2. **Create New Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the following:

   **Settings:**
   - **Name**: `weather-forecast-dashboard`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Plan**: `Free` (or your preferred plan)

   **Environment Variables** (optional):
   - `PYTHON_VERSION`: `3.11.0`

3. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your app
   - Wait for the build to complete (usually 2-5 minutes)

## File Structure for Deployment

Your deployment includes:
- `app.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `om_extract.py` - Weather data extraction module
- `siteList.csv` - Site location data
- `.streamlit/config.toml` - Streamlit configuration
- `render.yaml` - Render deployment configuration
- `.python-version` - Python version specification

## Important Notes

1. **Free Tier Limitations**
   - Services spin down after 15 minutes of inactivity
   - First request after inactivity may take 30-60 seconds
   - 750 hours/month free

2. **Custom Domain** (Optional)
   - Navigate to Settings → Custom Domain
   - Add your domain
   - Configure DNS as instructed

3. **Environment Variables**
   - Add sensitive data (API keys, secrets) in Dashboard → Environment
   - Never commit secrets to Git

4. **Monitoring**
   - Check logs in Dashboard → Logs
   - Monitor performance in Dashboard → Metrics

5. **Updates**
   - Push changes to your GitHub main branch
   - Render auto-deploys on push (can disable in settings)
   - Manual deploy: Dashboard → Manual Deploy

## Troubleshooting

### Build Fails
- Check Python version compatibility
- Verify all dependencies in `requirements.txt`
- Review build logs for specific errors

### App Won't Start
- Verify start command is correct
- Check that `app.py` exists in root or `docker/` directory
- Review application logs

### Port Issues
- Render automatically assigns `$PORT` environment variable
- Ensure start command includes `--server.port=$PORT`

### Data Loading Issues
- Verify `siteList.csv` is in the same directory as `app.py`
- Check file paths are relative, not absolute

## Support

- Render Documentation: https://render.com/docs
- Streamlit Documentation: https://docs.streamlit.io/
- GitHub Issues: Report problems in your repository

## Performance Optimization

For better performance on free tier:
1. Use `@st.cache_data` for expensive operations (already implemented)
2. Minimize API calls
3. Consider upgrading to paid plan for always-on service

## URLs

After deployment, your app will be available at:
- **Render URL**: `https://<your-app-name>.onrender.com`
- **Custom Domain**: Configure in Render dashboard (optional)
