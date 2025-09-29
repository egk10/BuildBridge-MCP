# 🔐 BuildBridge-MCP Security Configuration Guide

## Overview
This document outlines the secure configuration management for BuildBridge-MCP, ensuring sensitive credentials are never committed to version control.

## 🏗️ Current Security Structure

### ✅ Properly Secured (Not in Git)
- `.env` - Environment variables with API keys
- `config/client_secret.json` - Google OAuth credentials
- `config/credentials.json` - Service account keys and project configs
- `config/token.pickle` - OAuth access tokens
- `cache/` - Temporary data with project identifiers

### 📋 Configuration Hierarchy (Most to Least Secure)

1. **Environment Variables** (Highest Priority)
   - Set in `.env` file (local development)
   - Set in system environment (production)
   - Override all other configurations

2. **Local Configuration Files**
   - `config/credentials.json` - Project-specific settings
   - `config/client_secret.json` - OAuth credentials
   - Used when environment variables not available

3. **Template Files** (Safe to Commit)
   - `.env.template` - Shows required environment variables
   - `config/credentials.json.template` - Shows configuration structure

## 🚀 Recommended: Centralized Environment Variable Approach

### Step 1: Create Centralized .env Structure

```bash
# .env (NEVER commit - create locally)
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_PROJECT_ID=your-project-id

# Google Sheets Configuration
GOOGLE_SHEETS_PROJECT_72_PERTH=1iYDWJx_HSIzo6ORRDOTwkcfy-g0waKnu36THO7E52_k
GOOGLE_SHEETS_PROJECT_17175_YONGE_ST=1L6pKSAvq2_yN6SmQ11l80Q9jHJYG3dx_iLHffUJyDfU
GOOGLE_SHEETS_PROJECT_AZURE_ROAD=1pYlXf2-Je0uhxXkU_xWkIpLGXwvMP6SFM6oP-mL9BEg

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4-turbo
OPENAI_MAX_TOKENS=2000

# Application Settings
LOCAL_MODE=true
LOG_LEVEL=INFO
```

### Step 2: Update Application Code

Modify `src/production_mcp_integration.py` and other config loaders to prioritize environment variables:

```python
def load_secure_config():
    """Load configuration with environment variable priority"""
    config = {}

    # Google OAuth (from environment)
    config['google'] = {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'project_id': os.getenv('GOOGLE_PROJECT_ID'),
    }

    # Google Sheets (from environment)
    config['google_sheets'] = {
        '72_perth': os.getenv('GOOGLE_SHEETS_PROJECT_72_PERTH'),
        '17175_yonge_st': os.getenv('GOOGLE_SHEETS_PROJECT_17175_YONGE_ST'),
        'azure_road': os.getenv('GOOGLE_SHEETS_PROJECT_AZURE_ROAD'),
    }

    # OpenAI (from environment)
    config['openai'] = {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'model': os.getenv('OPENAI_MODEL', 'gpt-4-turbo'),
        'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '2000')),
    }

    # Fallback to local files if environment not set
    if not config['google']['client_id']:
        # Load from local config/client_secret.json
        pass

    return config
```

### Step 3: Docker Environment Variables

Update `deploy/docker-compose.yml`:

```yaml
services:
  buildbridge:
    env_file:
      - .env
    environment:
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./config:/app/config:ro  # Read-only mount for fallback
```

## 🔧 Migration Steps

### Phase 1: Environment Variable Setup
1. Create `.env` file with all sensitive values
2. Update application code to read from environment first
3. Test that environment variables override local files

### Phase 2: Remove Local Config Dependencies
1. Update all config loaders to use environment variables as primary source
2. Keep local files as fallback for development
3. Ensure production deployments use environment variables only

### Phase 3: Secure File Management
1. Move all sensitive files to `.env`
2. Remove local credential files from production deployments
3. Use Docker secrets or Kubernetes secrets for production

## 🛡️ Security Best Practices

### For Development
- Always use `.env` files (never commit)
- Use different credentials for dev/staging/production
- Rotate credentials regularly

### For Production
- Use environment variables or secret management systems
- Never mount credential files into containers
- Use Docker secrets or Kubernetes secrets
- Implement credential rotation policies

### For Repository
- Only commit template files (`.env.template`, `credentials.json.template`)
- Keep `.gitignore` updated with all sensitive paths
- Use GitGuardian or similar tools for automated scanning
- Regularly audit committed files for sensitive data

## 📋 Checklist

- [ ] `.env` file created with all sensitive values
- [ ] Application code updated to prioritize environment variables
- [ ] Docker configuration uses environment variables
- [ ] Local credential files removed from production
- [ ] `.gitignore` properly excludes sensitive files
- [ ] Template files committed for reference
- [ ] Git history cleaned of sensitive data (if needed)

## 🔍 Verification Commands

```bash
# Check for sensitive files in git
git ls-files | grep -E "\.env|client_secret|credentials\.json|token\.pickle"

# Check for hardcoded secrets in code
grep -r "sk-proj-\|GOCSPX-" src/

# Verify environment variables are loaded
python -c "import os; print('API Key loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```</content>
<parameter name="filePath">/home/egk/buildbridge-MCP/BuildBridge-MCP/docs/SECURITY_CONFIG_GUIDE.md