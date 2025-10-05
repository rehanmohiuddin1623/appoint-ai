# GitHub Secrets Setup Guide

To enable automated Docker image building and publishing, you need to set up GitHub repository secrets.

## Required Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions and add these secrets:

### 1. Docker Hub Credentials

**DOCKER_USERNAME**
- Your Docker Hub username
- Example: `rehanmohiuddin1623`

**DOCKER_TOKEN**
- Docker Hub access token (not your password!)
- Create at: https://hub.docker.com/settings/security
- Click "New Access Token"
- Give it a name like "GitHub Actions"
- Copy the generated token

## Setting Up Docker Hub Access Token

1. **Go to Docker Hub:** https://hub.docker.com
2. **Login** to your account
3. **Go to Account Settings:** Click your username → Account Settings
4. **Security tab:** https://hub.docker.com/settings/security
5. **Create New Access Token:**
   - Click "New Access Token"
   - Description: "GitHub Actions - Med Assist Agent"
   - Permissions: Read, Write, Delete
   - Click "Generate"
6. **Copy the token** - you won't see it again!

## Adding Secrets to GitHub

1. **Go to your repository:** https://github.com/rehanmohiuddin1623/appoint-ai
2. **Click Settings** (repository settings, not account)
3. **Secrets and variables** → **Actions**
4. **Click "New repository secret"**
5. **Add each secret:**

   **First Secret:**
   - Name: `DOCKER_USERNAME`
   - Secret: `rehanmohiuddin1623` (your Docker Hub username)
   
   **Second Secret:**
   - Name: `DOCKER_TOKEN`
   - Secret: (paste the access token from Docker Hub)

## Verification

After adding the secrets:

1. **Push to production branch:**
   ```bash
   git push origin production
   ```

2. **Check GitHub Actions:**
   - Go to your repository
   - Click "Actions" tab
   - You should see a workflow running
   - It will build and push the Docker image

3. **Verify on Docker Hub:**
   - Go to https://hub.docker.com/r/rehanmohiuddin1623/med-assist-agent
   - You should see your image with tags like `latest`, `production`

## Workflow Triggers

The GitHub Action will automatically run when:
- ✅ You push to `main` branch
- ✅ You push to `production` branch  
- ✅ You create a version tag (e.g., `v1.0.0`)
- ✅ Someone creates a pull request

## Docker Image Tags

The workflow creates these tags:
- `latest` - Latest production build
- `production` - Production branch
- `main` - Main branch  
- `v1.0.0` - Version tags
- `pr-123` - Pull request builds

## Troubleshooting

### Common Issues:

1. **"Invalid credentials" error:**
   - Check DOCKER_USERNAME is exactly your Docker Hub username
   - Regenerate DOCKER_TOKEN if needed
   - Make sure token has Read/Write permissions

2. **"Repository not found" error:**
   - Make sure the Docker Hub repository exists
   - Repository name in workflow should match: `rehanmohiuddin1623/med-assist-agent`

3. **Workflow doesn't trigger:**
   - Make sure you pushed to `production` or `main` branch
   - Check the workflow file is in `.github/workflows/` directory

### Test the Setup:

1. **Make a small change and push:**
   ```bash
   echo "# Test" >> README.md
   git add README.md
   git commit -m "Test GitHub Actions"
   git push origin production
   ```

2. **Watch the build:**
   - Go to GitHub → Actions tab
   - Click on the running workflow
   - Watch it build and push the image

3. **Check Docker Hub:**
   - Your image should appear at: https://hub.docker.com/r/rehanmohiuddin1623/med-assist-agent

## Optional: Webhook for Auto-Deployment

If you want automatic deployment to your VPS when new images are built:

1. **Add webhook secret to GitHub:**
   - Name: `WEBHOOK_SECRET`
   - Secret: A random string for security

2. **Configure webhook on VPS** (see VPS_DEPLOYMENT.md for details)

Once set up, every push to production will:
1. ✅ Build new Docker image
2. ✅ Push to Docker Hub
3. ✅ (Optional) Trigger deployment to VPS

Your Docker image will be available at:
`docker pull rehanmohiuddin1623/med-assist-agent:latest`