# 🔄 BuildBridge-MCP Security Migration Guide

## Overview
This guide outlines the migration from legacy configuration files to the new secure, centralized configuration system.

## ✅ What Was Done (Short-term Migration)

### 1. **SecureConfig System Implemented**
- Created `src/secure_config.py` - Centralized configuration manager
- Environment variables prioritized over local files
- Backward compatibility maintained for existing code

### 2. **Core Files Updated**
- `src/main.py` - Now uses SecureConfig with fallback
- `src/production_mcp_integration.py` - Updated load_config function
- Test scripts updated to use secure config

### 3. **Documentation Created**
- `docs/SECURITY_CONFIG_GUIDE.md` - Comprehensive security guide
- Updated `README.md` with security notices
- Updated `.env.template` with complete structure

---

## 🚀 Long-term Migration Plan

### Phase 1: Environment Variable Adoption (Current → 1 Week)

#### **Immediate Actions (This Week):**
1. **Set up environment variables** in development:
   ```bash
   # Copy and edit .env file
   cp .env.template .env
   # Edit .env with your actual credentials
   ```

2. **Test secure config loading**:
   ```bash
   python -c "from src.secure_config import get_config_manager; print(get_config_manager().get_config_summary())"
   ```

3. **Verify application works** with environment variables:
   ```bash
   # Test main.py
   python src/main.py

   # Test production server
   python src/production_mcp_integration.py --mode test
   ```

#### **Development Environment:**
- Use `.env` files for local development
- Keep local config files as backup
- Test both secure and legacy loading

### Phase 2: Production Environment Migration (1-2 Weeks)

#### **Docker Deployment:**
1. **Update docker-compose.yml**:
   ```yaml
   services:
     buildbridge:
       env_file:
         - .env
       environment:
         - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
         - OPENAI_API_KEY=${OPENAI_API_KEY}
   ```

2. **Remove credential files** from containers:
   ```dockerfile
   # In Dockerfile - DON'T copy credential files
   # COPY config/ ./config/  # Remove this line
   ```

3. **Use Docker secrets** for production:
   ```yaml
   services:
     buildbridge:
       secrets:
         - google_credentials
         - openai_key
   ```

#### **Kubernetes Deployment:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: buildbridge-secrets
type: Opaque
data:
  google-client-id: <base64-encoded>
  openai-api-key: <base64-encoded>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: buildbridge
spec:
  template:
    spec:
      containers:
      - env:
        - name: GOOGLE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: buildbridge-secrets
              key: google-client-id
```

### Phase 3: Legacy Cleanup (2-4 Weeks)

#### **Remove Legacy Dependencies:**
1. **Delete local credential files** from production:
   ```bash
   rm config/client_secret.json
   rm config/credentials.json
   rm config/token.pickle
   ```

2. **Update all code** to require environment variables:
   ```python
   # In secure_config.py - make environment variables mandatory
   if not config.client_id:
       raise ValueError("GOOGLE_CLIENT_ID environment variable required")
   ```

3. **Remove fallback code** from load_config functions

#### **Update CI/CD Pipelines:**
- Use secret management systems (GitHub Secrets, AWS Secrets Manager, etc.)
- Remove credential files from build artifacts
- Add security scanning for hardcoded secrets

### Phase 4: Monitoring & Maintenance (Ongoing)

#### **Security Monitoring:**
- Regular credential rotation
- Monitor for exposed secrets
- Audit access logs
- Security scanning in CI/CD

#### **Configuration Validation:**
```python
# Add to startup checks
from secure_config import get_config_manager
config_manager = get_config_manager()
issues = config_manager.validate_config()
if issues:
    logger.error(f"Configuration issues: {issues}")
    exit(1)
```

---

## 🔧 Implementation Details

### **Current State (Backward Compatible):**
```python
# This still works (legacy support)
config = load_config()  # Uses secure config internally

# New way (recommended)
from secure_config import load_secure_config
config = load_secure_config()
```

### **Environment Variable Mapping:**
```bash
# .env file
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_SHEETS_PROJECT_72_PERTH=1iYDWJx_HSIzo6ORRDOTwkcfy-g0waKnu36THO7E52_k
OPENAI_API_KEY=sk-proj-your-key
```

### **Configuration Priority:**
1. **Environment Variables** (most secure)
2. **SecureConfig Manager** (unified approach)
3. **Local Files** (development fallback)
4. **Templates** (failsafe defaults)

---

## 🧪 Testing Migration

### **Test Commands:**
```bash
# Test secure config loading
python -c "from src.secure_config import get_config_manager; cm = get_config_manager(); print(cm.get_config_summary())"

# Test legacy compatibility
python -c "from src.main import load_config; config = load_config(); print('Config loaded:', bool(config))"

# Test production integration
python src/production_mcp_integration.py --mode test

# Test with environment variables
OPENAI_API_KEY=test-key python -c "from secure_config import load_secure_config; print(load_secure_config()['openai'].api_key)"
```

### **Validation Checklist:**
- [ ] Environment variables load correctly
- [ ] Local files work as fallback
- [ ] Application starts with both methods
- [ ] Docker builds without credential files
- [ ] Production deployment uses secrets
- [ ] No hardcoded credentials in code

---

## 🚨 Security Considerations

### **During Migration:**
- **Never commit** `.env` files
- **Rotate credentials** if exposed
- **Use different credentials** for dev/staging/production
- **Monitor for exposed secrets**

### **Post-Migration:**
- **Environment variables only** in production
- **Secret management systems** for credentials
- **Regular security audits**
- **Automated secret scanning**

---

## 📋 Timeline Summary

| Phase | Timeline | Actions | Status |
|-------|----------|---------|--------|
| **Short-term** | Now | SecureConfig implementation | ✅ Complete |
| **Phase 1** | This week | Environment variable adoption | 🔄 In Progress |
| **Phase 2** | 1-2 weeks | Production deployment updates | ⏳ Planned |
| **Phase 3** | 2-4 weeks | Legacy cleanup | ⏳ Planned |
| **Phase 4** | Ongoing | Security monitoring | ⏳ Planned |

---

## 🆘 Troubleshooting

### **Common Issues:**

**"Secure config failed, falling back to legacy method"**
- Environment variables not set
- Check `.env` file exists and is loaded
- Verify variable names match `.env.template`

**"GOOGLE_CLIENT_ID not configured"**
- Set environment variables in `.env`
- Or ensure local config files exist for development

**"ImportError: secure_config not found"**
- Add `src/` to Python path
- Check file exists: `ls src/secure_config.py`

### **Debug Commands:**
```bash
# Check environment variables
env | grep -E "(GOOGLE|OPENAI)"

# Test config loading
python -c "import sys; sys.path.append('src'); from secure_config import get_config_manager; print(get_config_manager().validate_config())"

# Check .env loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('API Key loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```

---

## 📞 Support

- **Security Issues**: Immediately rotate credentials, check for exposure
- **Migration Help**: Use the test commands above
- **Documentation**: See `docs/SECURITY_CONFIG_GUIDE.md`

**Remember: Security is a journey, not a destination. Regular audits and updates are essential.** 🔒</content>
<parameter name="filePath">/home/egk/buildbridge-MCP/BuildBridge-MCP/docs/MIGRATION_GUIDE.md