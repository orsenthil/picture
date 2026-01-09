# Deployment Guide

This guide covers deploying the Picture of the Day application to production, including the website/API and browser extension.

## Deployment Workflow

The recommended deployment order is:
1. **Deploy Website/API** → Test website and API
2. **Package Browser Extension** → Test extension → Publish extension

---

## Part 1: Deploy Website/API to Kubernetes

### Prerequisites

- Docker installed and configured
- Access to DigitalOcean Container Registry (or your container registry)
- Kubernetes cluster access with kubectl configured
- All secrets and configmaps configured in Kubernetes

### Step 1: Build and Push Docker Image

```bash
# Build the Docker image
docker build -t registry.digitalocean.com/orsenthil/pictureoftheday:latest .

# Push to registry
docker push registry.digitalocean.com/orsenthil/pictureoftheday:latest
```

**Note:** If you want to tag a specific version:
```bash
VERSION="v0.0.7"
docker build -t registry.digitalocean.com/orsenthil/pictureoftheday:${VERSION} .
docker push registry.digitalocean.com/orsenthil/pictureoftheday:${VERSION}
# Update deployment.yaml to use the version tag
```

### Step 2: Apply Kubernetes Configuration

**Option A: Using the deployment script (Recommended)**

```bash
# Apply all configs and restart deployment
cd k8s
./deploy.sh --apply

# Or if configs are already applied, just restart to pull new image
./deploy.sh
```

**Option B: Manual apply**

```bash
# Apply all Kubernetes resources
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/cronjob.yaml
```

**When to use the script:**
- **First time deployment:** Use `./deploy.sh --apply` to apply all configs
- **Code changes only (no k8s changes):** Use `./deploy.sh` to restart and pull new image
- **K8s config changes:** Use `./deploy.sh --apply` to apply changes and restart
- **Only update k8s configs (no restart):** Use `./deploy.sh --apply-only`

### Step 3: Verify Deployment

```bash
# Check deployment status
kubectl get pods -n pictureoftheday

# Check if pods are running
kubectl get pods -n pictureoftheday -l app=pictureoftheday

# View deployment logs
kubectl logs -n pictureoftheday -l app=pictureoftheday --tail=50

# Check service
kubectl get svc -n pictureoftheday

# Check ingress
kubectl get ingress -n pictureoftheday
```

### Step 4: Run Migrations (if needed)

Migrations should run automatically via initContainers, but you can also run them manually:

```bash
# Run migrations manually
kubectl exec -n pictureoftheday -it deployment/pictureoftheday -- python manage.py migrate
```

---

## Part 2: Test Website and API

### Test Website

1. **Visit the website:**
   ```
   https://picture.learntosolveit.com/
   ```

2. **Verify functionality:**
   - Page loads correctly
   - Picture displays
   - Source selector dropdown works
   - Can switch between sources
   - Settings panel works
   - All sources are listed correctly

3. **Test source enable/disable:**
   - Go to admin: `https://picture.learntosolveit.com/admin/`
   - Enable/disable a source
   - Reload the main page (hard refresh: Ctrl+Shift+R)
   - Verify dropdown updates immediately

### Test API Endpoints

```bash
# Test sources endpoint
curl https://picture.learntosolveit.com/api/pictures/sources/ | python3 -m json.tool

# Test today endpoint for each source
curl https://picture.learntosolveit.com/api/pictures/today/apod/ | python3 -m json.tool
curl https://picture.learntosolveit.com/api/pictures/today/wikipedia/ | python3 -m json.tool
curl https://picture.learntosolveit.com/api/pictures/today/bing/ | python3 -m json.tool

# Test list endpoint
curl https://picture.learntosolveit.com/api/pictures/list/bing/ | python3 -m json.tool
```

### Test Admin Actions

1. **Login to admin:**
   ```
   https://picture.learntosolveit.com/admin/
   ```

2. **Test fetch actions:**
   - Go to **Pictures → Source Configurations**
   - Select a source
   - Use action: **"Fetch pictures for selected sources"**
   - Verify success message
   - Check that picture was fetched

3. **Test fetch all enabled sources:**
   - Use action: **"Fetch pictures for all enabled sources"**
   - Verify all sources are fetched

4. **Test picture refetch:**
   - Go to **Pictures → Picture of the days**
   - Select a picture
   - Use action: **"Re-fetch and re-process selected pictures"**
   - Verify picture is updated

---

## Part 3: Package Browser Extension

### Step 1: Update Production Config

Ensure `extension/config.production.js` has the correct production API URL:

```javascript
const CONFIG = {
    BACKEND_API_URL: 'https://picture.learntosolveit.com/api'
};
```

### Step 2: Package Extension

```bash
# Make script executable (if needed)
chmod +x package-extension.sh

# Package the extension
./package-extension.sh
```

This creates `picture-of-the-day-extension.zip` in the project root.

### Step 3: Verify Package Contents

```bash
# List contents of the zip
unzip -l picture-of-the-day-extension.zip

# Verify required files are present:
# - manifest.json
# - config.js (should be production config)
# - newtab.html
# - newtab.js
# - styles.css
# - gtag-init.js
# - icons/ (directory)
```

---

## Part 4: Test Browser Extension

### Load Extension in Browser

#### Chrome/Edge:

1. Open `chrome://extensions/` (or `edge://extensions/`)
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Select the `extension/` directory (NOT the zip file)
5. Extension should load

#### Firefox:

1. Open `about:debugging`
2. Click **This Firefox**
3. Click **Load Temporary Add-on**
4. Select `extension/manifest.json`
5. Extension should load

### Test Extension Functionality

1. **Open a new tab** - should show picture of the day
2. **Test source switching:**
   - Open settings
   - Change picture source
   - Verify picture updates
3. **Test all sources:**
   - Switch to APOD
   - Switch to Wikipedia
   - Switch to Bing
   - Verify each loads correctly
4. **Test settings:**
   - Toggle description visibility
   - Toggle random on new tab
   - Toggle dimensions overlay
5. **Test with production API:**
   - Verify extension connects to `https://picture.learntosolveit.com/api`
   - Check browser console for any errors
   - Verify API calls are successful

### Test Extension Package (Production Build)

1. **Extract the zip file:**
   ```bash
   unzip picture-of-the-day-extension.zip -d test-extension/
   ```

2. **Verify production config:**
   ```bash
   cat test-extension/config.js
   # Should show production API URL
   ```

3. **Load extracted extension:**
   - Use the extracted `test-extension/` directory
   - Load as unpacked extension
   - Test all functionality

---

## Part 5: Publish Browser Extension

### Chrome Web Store

1. **Prepare for submission:**
   - Ensure version number is updated in `extension/manifest.json`
   - Update changelog/description if needed
   - Test extension thoroughly

2. **Create zip package:**
   ```bash
   ./package-extension.sh
   ```

3. **Submit to Chrome Web Store:**
   - Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
   - Upload `picture-of-the-day-extension.zip`
   - Fill in store listing details
   - Submit for review

### Firefox Add-ons (AMO)

1. **Package for Firefox:**
   - Firefox uses the same package format
   - Use the same zip file

2. **Submit to AMO:**
   - Go to [Firefox Add-on Developer Hub](https://addons.mozilla.org/developers/)
   - Upload `picture-of-the-day-extension.zip`
   - Fill in listing details
   - Submit for review

### Edge Add-ons

1. **Submit to Microsoft Edge Add-ons:**
   - Go to [Partner Center](https://partner.microsoft.com/dashboard)
   - Upload the same zip file
   - Submit for review

---

## Rollback Procedures

### Rollback Website/API

If issues are detected after deployment:

```bash
# Rollback to previous image version
kubectl set image deployment/pictureoftheday \
  django=registry.digitalocean.com/orsenthil/pictureoftheday:previous-version \
  -n pictureoftheday

# Or rollback deployment (reverts to previous revision)
kubectl rollout undo deployment/pictureoftheday -n pictureoftheday

# Check rollout history
kubectl rollout history deployment/pictureoftheday -n pictureoftheday
```

### Rollback Browser Extension

- If extension is published, submit a new version with fixes
- If extension is in review, you can cancel and resubmit
- For unpacked extensions, simply reload the previous version

---

## Troubleshooting

### Website/API Issues

```bash
# Check pod logs
kubectl logs -n pictureoftheday -l app=pictureoftheday --tail=100

# Check pod status
kubectl describe pod -n pictureoftheday -l app=pictureoftheday

# Check ingress
kubectl describe ingress -n pictureoftheday pictureoftheday-ingress

# Test database connection
kubectl exec -n pictureoftheday -it deployment/pictureoftheday -- python manage.py dbshell
```

### Extension Issues

- Check browser console for errors
- Verify API endpoints are accessible
- Check network tab for failed requests
- Verify config.js has correct API URL
- Clear extension storage and reload

---

## Version Management

### Update Version Numbers

1. **Backend version:** Update in `backend/settings.py` or use git tags
2. **Extension version:** Update in `extension/manifest.json` and `extension/manifest.production.json`

### Tagging Releases

```bash
# Create git tag
git tag -a v0.0.7 -m "Release version 0.0.7"
git push origin v0.0.7

# Tag Docker image
docker tag registry.digitalocean.com/orsenthil/pictureoftheday:latest \
  registry.digitalocean.com/orsenthil/pictureoftheday:v0.0.7
docker push registry.digitalocean.com/orsenthil/pictureoftheday:v0.0.7
```

---

## Quick Reference

### Common Commands

```bash
# Build and push Docker image
docker build -t registry.digitalocean.com/orsenthil/pictureoftheday:latest .
docker push registry.digitalocean.com/orsenthil/pictureoftheday:latest

# Deploy to Kubernetes (using script)
cd k8s
./deploy.sh --apply        # First time or when k8s configs changed
./deploy.sh                # When only code changed (restart to pull new image)

# Or apply Kubernetes configs manually
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n pictureoftheday

# Package extension
./package-extension.sh

# Run tests
python manage.py test
```

### Important URLs

- **Production Website:** https://picture.learntosolveit.com/
- **Production API:** https://picture.learntosolveit.com/api/
- **Admin Panel:** https://picture.learntosolveit.com/admin/

---

## Notes

- Always test locally before deploying to production
- Run all tests before deployment: `python manage.py test`
- Keep backups of previous Docker images
- Document any breaking changes
- Update version numbers before publishing extensions


