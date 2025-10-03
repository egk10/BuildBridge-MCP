# Production Deployment Guide

**Date:** October 3, 2025  
**Version:** 2.0 (Post .env-only Configuration)

---

## Quick Start

### 1. Copy Environment Template

```bash
cp .env.template .env
```

### 2. Update Production Values

Edit `.env` with your production credentials:

```bash
# GOOGLE OAUTH (Production Credentials)
GOOGLE_CLIENT_ID=your-production-client-id
GOOGLE_CLIENT_SECRET=your-production-client-secret
GOOGLE_PROJECT_ID=your-production-project

# PROJECTS (Add all production projects)
GOOGLE_SHEETS_PROJECT_1_NAME=ProjectAlpha
GOOGLE_SHEETS_PROJECT_1_ID=production-sheet-id-1
GOOGLE_SHEETS_PROJECT_2_NAME=ProjectBeta
GOOGLE_SHEETS_PROJECT_2_ID=production-sheet-id-2

# OPENAI (Production API Key)
OPENAI_API_KEY=your-production-openai-key
OPENAI_MODEL=gpt-4o

# PRODUCTION SETTINGS
LOCAL_MODE=false
LOG_LEVEL=WARNING
DEBUG=false
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### 3. Deploy

```bash
# Install dependencies
pip install -r requirements-production.txt

# Set Python path
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"

# Start server (with process manager recommended)
nohup python src/production_mcp_integration.py \
    --mode server \
    --host 0.0.0.0 \
    --port 8000 \
    > logs/server.log 2>&1 &
```

---

## Production Checklist

### Security
- ✅ Generated strong OAuth credentials for production
- ✅ `.env` file has restricted permissions (chmod 600)
- ✅ `.env` is gitignored (never committed)
- ✅ API keys are production-specific (not shared with dev)
- ✅ Server runs with limited user permissions

### Configuration
- ✅ All project spreadsheets created in production Google Drive
- ✅ Tab names match defaults (Project Summary, GCA Stats)
- ✅ OAuth consent screen approved for production domain
- ✅ `LOCAL_MODE=false` for production
- ✅ `LOG_LEVEL=WARNING` or `ERROR` for production

### Infrastructure
- ✅ Process manager configured (systemd, supervisor, or PM2)
- ✅ Reverse proxy configured (nginx recommended)
- ✅ SSL/TLS certificates installed
- ✅ Firewall rules configured
- ✅ Monitoring and alerting set up

### Testing
- ✅ Cache refresh tested with production data
- ✅ API endpoints verified working
- ✅ Authentication flow tested
- ✅ All projects accessible via Web Chat V2
- ✅ Load testing completed

---

## Adding New Production Projects

### Step 1: Create Google Sheet
1. Create new spreadsheet in production Google Drive
2. Copy spreadsheet ID from URL
3. Ensure tabs named: "Project Summary", "GCA Stats"

### Step 2: Update .env
```bash
# Add to .env (increment number)
GOOGLE_SHEETS_PROJECT_4_NAME=NewProject
GOOGLE_SHEETS_PROJECT_4_ID=spreadsheet-id-here
```

### Step 3: Refresh & Restart
```bash
python scripts/refresh_from_live_sheets.py
systemctl restart buildbridge-mcp  # or your process manager
```

**That's it!** No JSON editing required.

---

## Process Management

### Using systemd (Recommended for Linux)

Create `/etc/systemd/system/buildbridge-mcp.service`:

```ini
[Unit]
Description=BuildBridge MCP Server
After=network.target

[Service]
Type=simple
User=buildbridge
Group=buildbridge
WorkingDirectory=/opt/buildbridge-mcp
Environment="PYTHONPATH=/opt/buildbridge-mcp/src"
ExecStart=/opt/buildbridge-mcp/buildbridge_venv/bin/python \
    /opt/buildbridge-mcp/src/production_mcp_integration.py \
    --mode server --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=append:/var/log/buildbridge-mcp/server.log
StandardError=append:/var/log/buildbridge-mcp/error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable buildbridge-mcp
sudo systemctl start buildbridge-mcp
sudo systemctl status buildbridge-mcp
```

---

## Nginx Reverse Proxy (Recommended)

Create `/etc/nginx/sites-available/buildbridge-mcp`:

```nginx
server {
    listen 80;
    server_name buildbridge.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name buildbridge.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/buildbridge.crt;
    ssl_certificate_key /etc/ssl/private/buildbridge.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/buildbridge-mcp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

### View Logs

```bash
# Using systemd
sudo journalctl -u buildbridge-mcp -f

# Or direct log files
tail -f logs/server.log
```

### Monitor API

```bash
# Check projects endpoint
curl http://localhost:8000/api/projects | jq

# Check specific project
curl http://localhost:8000/api/projects/ProjectAlpha | jq
```

---

## Backup Strategy

### Configuration Backup

```bash
# Backup .env (encrypted)
gpg --symmetric --cipher-algo AES256 .env
# Store .env.gpg securely off-server
```

### Cache Backup

```bash
# Backup cache directory
tar -czf cache-backup-$(date +%Y%m%d).tar.gz cache/
```

### Automated Backups

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * cd /opt/buildbridge-mcp && tar -czf /backup/cache-$(date +\%Y\%m\%d).tar.gz cache/
```

---

## Troubleshooting

### Server Won't Start

1. **Check logs:**
   ```bash
   tail -100 logs/server.log
   ```

2. **Verify .env:**
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('Projects:', [os.getenv(f'GOOGLE_SHEETS_PROJECT_{i}_NAME') for i in range(1,10) if os.getenv(f'GOOGLE_SHEETS_PROJECT_{i}_NAME')])"
   ```

3. **Test configuration:**
   ```bash
   python -c "from src.secure_config import build_project_manifest_from_env; manifest = build_project_manifest_from_env(); print(f'Found {len(manifest)} projects')"
   ```

### Projects Not Loading

1. **Check Google Sheets access:**
   ```bash
   python scripts/refresh_from_live_sheets.py
   ```

2. **Verify OAuth token:**
   ```bash
   ls -lh config/token.pickle
   # If expired, delete and re-authenticate
   ```

3. **Check spreadsheet IDs:**
   - Ensure IDs in .env match actual spreadsheets
   - Verify OAuth credentials have access

### Performance Issues

1. **Enable caching:**
   - Cache is enabled by default
   - Check `cache/` directory exists

2. **Monitor resource usage:**
   ```bash
   htop  # or top
   ```

3. **Review log level:**
   - Set `LOG_LEVEL=ERROR` for production
   - Reduces I/O overhead

---

## Scaling Considerations

### Horizontal Scaling

- Run multiple instances behind load balancer
- Share cache via Redis (future enhancement)
- Use same `.env` across all instances

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Default configuration handles ~100 req/min
- For higher loads, consider async workers

### Database Backend (Future)

- Currently file-based cache
- Database integration planned for v3.0
- Will enable multi-instance caching

---

## Security Best Practices

1. **Credentials Management**
   - Use secret management service (AWS Secrets Manager, Azure Key Vault)
   - Rotate API keys quarterly
   - Never commit `.env` to git

2. **Network Security**
   - Use firewall (ufw, iptables)
   - Restrict port 8000 to localhost
   - Access only via reverse proxy

3. **Access Control**
   - Run as limited user (not root)
   - Restrict file permissions (chmod 600 .env)
   - Use OAuth consent screen restrictions

4. **Monitoring**
   - Set up alerts for errors
   - Monitor API usage
   - Track failed authentication attempts

---

## Rollback Procedure

If issues occur after deployment:

```bash
# 1. Stop server
systemctl stop buildbridge-mcp

# 2. Restore previous .env
cp .env.backup .env

# 3. Restore previous code
git checkout previous-stable-tag

# 4. Restart server
systemctl start buildbridge-mcp

# 5. Verify
curl http://localhost:8000/health
```

---

## Support

- **Documentation:** `docs/` directory
- **Configuration:** `docs/ENV_ONLY_CONFIG_COMPLETE.md`
- **Security:** `docs/SECURITY_CONFIG_GUIDE.md` (if exists)
- **Issues:** GitHub Issues

---

## Version History

- **v2.0** (Oct 3, 2025) - .env-only configuration system
- **v1.0** (Sep 2025) - Initial production release

---

**Status:** ✅ Production Ready  
**Last Updated:** October 3, 2025
