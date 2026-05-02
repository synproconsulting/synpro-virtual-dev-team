# Railway Integration Setup Guide

This guide will help you set up the Railway integration for the UAT Deploy tab in the Control Centre.

## Prerequisites

- Railway account with API access
- Railway project(s) deployed
- Backend server running (`uat/backend`)
- Control Centre frontend running (`control-centre`)

## Step 1: Get Railway API Token

1. **Log in to Railway**
   - Visit https://railway.app
   - Sign in to your account

2. **Navigate to Account Settings**
   - Click on your profile in the top right
   - Select "Account Settings"

3. **Create API Token**
   - Go to the "Tokens" section
   - Click "Create Token"
   - Give it a descriptive name (e.g., "UAT Control Centre")
   - Select the following permissions:
     - ✅ Read projects
     - ✅ Read services
     - ✅ Read deployments
     - ✅ Trigger deployments
   - Click "Create"

4. **Copy the Token**
   - Copy the generated token immediately
   - **Important:** You won't be able to see it again!

## Step 2: Configure Backend

1. **Navigate to backend directory**
   ```bash
   cd uat/backend
   ```

2. **Copy environment template**
   ```bash
   cp .env.example .env
   ```

3. **Add Railway API token**
   
   Open `.env` and add your token:
   ```bash
   RAILWAY_API_TOKEN=your-actual-token-here
   ```

4. **Restart backend server**
   ```bash
   # If using uvicorn directly
   uvicorn main:app --reload
   
   # If using docker-compose
   docker-compose restart backend
   ```

5. **Verify configuration**
   ```bash
   curl http://localhost:8000/api/railway/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "configured": true,
     "projects_count": 1
   }
   ```

## Step 3: Configure Frontend (Optional)

The frontend will work without additional configuration, but you can set a default project ID for convenience.

1. **Get your Railway Project ID**
   - Open your Railway project
   - Go to Settings
   - Copy the Project ID

2. **Navigate to frontend directory**
   ```bash
   cd control-centre
   ```

3. **Copy environment template (if not already done)**
   ```bash
   cp .env.example .env
   ```

4. **Add configuration**
   
   Open `.env` and add:
   ```bash
   # Backend API URL (should already be set)
   VITE_API_BASE_URL=http://localhost:8000
   
   # Optional: Auto-select this project on load
   VITE_RAILWAY_PROJECT_ID=your-project-id-here
   ```

5. **Restart frontend**
   ```bash
   npm run dev
   ```

## Step 4: Test the Integration

1. **Open Control Centre**
   - Navigate to http://localhost:5173 (or your frontend URL)
   - Click on the "UAT Deploy" tab

2. **Check health indicator**
   - Look for the "Connected" badge in green at the top right
   - If you see "Disconnected" in red, check your backend configuration

3. **Select a project**
   - Choose a project from the dropdown
   - Select an environment (production, staging, UAT, development)

4. **View deployments**
   - You should see cards showing your recent deployments
   - Each card shows:
     - Service name
     - Deployment status (color-coded)
     - Deployment ID
     - Timestamps
     - Service URL (if available)

5. **Test auto-refresh**
   - Enable the "Auto-refresh (30s)" checkbox
   - Make a deployment in Railway
   - Watch the status update automatically in the Control Centre

## Troubleshooting

### "Railway API not configured" error

**Problem:** Backend can't find the Railway API token

**Solutions:**
1. Verify `RAILWAY_API_TOKEN` is set in `uat/backend/.env`
2. Make sure there are no extra spaces or quotes around the token
3. Restart the backend server after adding the token
4. Check the token hasn't expired

**Verify token is loaded:**
```bash
# From uat/backend directory
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Token:', 'SET' if os.getenv('RAILWAY_API_TOKEN') else 'NOT SET')"
```

### "Disconnected" health badge

**Problem:** Frontend can't connect to backend or Railway API

**Check backend is running:**
```bash
curl http://localhost:8000/health
```

**Check Railway integration:**
```bash
curl http://localhost:8000/api/railway/health
```

**Solutions:**
1. Ensure backend is running on the correct port
2. Check `VITE_API_BASE_URL` in frontend `.env` matches backend URL
3. Verify Railway API token is valid
4. Check backend logs for errors

### No projects showing

**Problem:** Projects dropdown is empty

**Check projects endpoint:**
```bash
curl http://localhost:8000/api/railway/projects
```

**Solutions:**
1. Verify your Railway account has projects
2. Check the API token has "Read projects" permission
3. Ensure the Railway account associated with the token has access to projects
4. Review backend logs for API errors

### No deployments showing

**Problem:** Selected a project but no deployments appear

**Check environment exists:**
- Verify the environment name (production, staging, etc.) exists in your Railway project
- Railway environment names are case-insensitive in the UI but case-sensitive in API

**Check deployments endpoint:**
```bash
curl "http://localhost:8000/api/railway/projects/YOUR_PROJECT_ID/environments/production/deployments"
```

**Solutions:**
1. Ensure services in the project have been deployed to the selected environment
2. Try selecting a different environment
3. Check backend logs for GraphQL errors

### CORS errors in browser console

**Problem:** Browser blocks requests to backend

**Solutions:**
1. Ensure `FRONTEND_URL` is set in `uat/backend/.env`
2. Verify frontend URL matches exactly (including http/https and port)
3. Add multiple frontend URLs if needed:
   ```bash
   FRONTEND_URL=http://localhost:5173,http://localhost:3000
   ```
4. For development, you can temporarily allow all origins:
   ```bash
   FRONTEND_URL=*
   ALLOW_CORS_WILDCARD=true
   ```
   **Warning:** Never use wildcard CORS in production!

### Slow API responses

**Problem:** Requests to Railway API are slow or timing out

**Solutions:**
1. Check your internet connection
2. Verify Railway API is operational: https://status.railway.app
3. Increase timeout in `railway_client.py` if needed (default is 30 seconds)
4. Consider caching responses for frequently accessed data

## Testing the Setup

Run these commands to verify everything is working:

### 1. Backend Health Check
```bash
curl http://localhost:8000/api/railway/health
```
Expected: `"status": "healthy"`

### 2. List Projects
```bash
curl http://localhost:8000/api/railway/projects
```
Expected: JSON with your Railway projects

### 3. List Services
```bash
# Replace PROJECT_ID with your actual project ID
curl http://localhost:8000/api/railway/projects/PROJECT_ID/services
```
Expected: JSON with services in the project

### 4. Get Deployments
```bash
# Replace PROJECT_ID with your actual project ID
curl "http://localhost:8000/api/railway/projects/PROJECT_ID/environments/production/deployments"
```
Expected: JSON with recent deployments

## Production Deployment

When deploying to production:

1. **Use environment variables from hosting platform**
   - Railway: Set in Service Variables
   - Heroku: Use Config Vars
   - Docker: Use environment files or secrets

2. **Never commit tokens to git**
   - Add `.env` to `.gitignore` (already done)
   - Use secrets management for sensitive values

3. **Rotate tokens regularly**
   - Set a reminder to rotate Railway API tokens every 90 days
   - Keep track of where tokens are used

4. **Monitor API usage**
   - Railway has rate limits
   - Implement caching if you hit limits
   - Consider reducing auto-refresh frequency in production

5. **Set up proper CORS**
   ```bash
   # Backend .env for production
   ENVIRONMENT=production
   FRONTEND_URL=https://your-production-domain.com
   ```

## Next Steps

After successful setup:

1. **Explore the UI**
   - Try different environments
   - Enable auto-refresh
   - View deployment details

2. **Read the documentation**
   - Full API reference: `docs/RAILWAY_INTEGRATION.md`
   - Understanding deployment statuses
   - Error handling

3. **Consider enhancements**
   - Set up deployment notifications
   - Add monitoring alerts
   - Implement deployment triggers from UI

## Getting Help

If you encounter issues:

1. **Check logs**
   - Backend logs: `uat/backend/logs/` or console output
   - Frontend console: Browser developer tools
   - Railway logs: Railway dashboard

2. **Verify configuration**
   - Run all test commands above
   - Compare your `.env` with `.env.example`

3. **Review documentation**
   - `docs/RAILWAY_INTEGRATION.md` - Full integration docs
   - Railway API docs: https://docs.railway.app/reference/public-api

4. **Contact support**
   - Open an issue with:
     - What you tried
     - Error messages (sanitized - remove tokens!)
     - Relevant logs
     - Output of test commands

## Quick Reference

### Environment Variables

**Backend (`uat/backend/.env`):**
```bash
RAILWAY_API_TOKEN=your-token-here
FRONTEND_URL=http://localhost:5173
```

**Frontend (`control-centre/.env`):**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_RAILWAY_PROJECT_ID=your-project-id  # Optional
```

### Important URLs

- Railway Dashboard: https://railway.app
- Railway API Tokens: https://railway.app/account/tokens
- Railway Status: https://status.railway.app
- Railway API Docs: https://docs.railway.app/reference/public-api

### Key Commands

```bash
# Test backend health
curl http://localhost:8000/api/railway/health

# Test projects
curl http://localhost:8000/api/railway/projects

# Start backend
cd uat/backend && uvicorn main:app --reload

# Start frontend
cd control-centre && npm run dev
```
