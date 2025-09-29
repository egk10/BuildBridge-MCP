# Formula Awareness Runbook

## Overview
This runbook provides operational procedures for managing the formula-awareness system in BuildBridge-MCP. The formula-awareness system enhances AI understanding of spreadsheet business logic through formula extraction, dependency analysis, and what-if simulation.

## System Architecture

### Components
- **EnhancedGoogleSheetsConnector**: Extracts formulas, dependencies, and metadata from Google Sheets
- **FormulaClassifier**: Categorizes formulas by business rule type
- **WhatIfSimulator**: Performs impact analysis for hypothetical changes
- **FormulaAwareAIService**: Integrates formula context into AI responses
- **Prometheus Metrics**: Monitors system health and performance

### Key Metrics
- `formula_extraction_success_rate`: Percentage of successful formula extractions
- `formula_extraction_duration_seconds`: Time taken for formula extraction
- `circular_reference_count`: Number of circular references detected
- `dependency_graph_health`: Health score of dependency graphs (0.0-1.0)
- `ai_formula_accuracy`: AI accuracy for formula-related queries

## Operational Procedures

### Monitoring

#### Dashboard Access
- **Grafana**: http://localhost:3003 (admin/admin)
- **Prometheus**: http://localhost:9092

#### Key Alerts to Monitor
- `FormulaExtractionFailureRateHigh`: Success rate < 95% for 5+ minutes
- `CircularReferencesDetected`: Any circular references found
- `DependencyGraphUnhealthy`: Health score < 0.9 for 5+ minutes
- `AIAccuracyDegraded`: AI accuracy < 75% for 10+ minutes

### Troubleshooting

#### Formula Extraction Failures

**Symptoms:**
- `FormulaExtractionFailureRateHigh` alert firing
- AI responses lacking formula context

**Diagnosis:**
```bash
# Check recent extraction logs
tail -f logs/server.log | grep "formula.*extraction"

# Test extraction manually
PYTHONPATH=src python3 -c "
from connectors.enhanced_google_sheets_connector import EnhancedGoogleSheetsConnector
import json
config = json.load(open('config/credentials.json'))
connector = EnhancedGoogleSheetsConnector(config)
# Test with known working sheet ID
result = connector.get_comprehensive_sheet_context('YOUR_SHEET_ID')
print('Success:', len(result.get('formulas', {})) > 0)
"
```

**Resolution:**
1. Check Google Sheets API quotas and credentials
2. Verify sheet permissions and sharing settings
3. Clear cache if corrupted: `rm -rf cache/normalized/formulas/*`
4. Restart service if API client is stale

#### Circular Reference Issues

**Symptoms:**
- `CircularReferencesDetected` alert firing
- Dependency analysis warnings in logs

**Diagnosis:**
```bash
# Check for circular references in recent extractions
PYTHONPATH=src python3 -c "
from schema_discovery import detect_circular_references
# Load dependency graph from cache or recent extraction
# Print any cycles found
"
```

**Resolution:**
1. Review spreadsheet design for unnecessary circular references
2. Use iterative calculation settings in Google Sheets if cycles are expected
3. Document business justification for circular references
4. Update monitoring thresholds if cycles are expected

#### AI Accuracy Degradation

**Symptoms:**
- `AIAccuracyDegraded` alert firing
- Users reporting poor formula-related responses

**Diagnosis:**
```bash
# Check AI service logs
grep "formula.*context" logs/server.log | tail -20

# Test AI accuracy manually
PYTHONPATH=src python3 -c "
from ai.formula_aware_ai_service import FormulaAwareAIService
# Test with sample formula context
"
```

**Resolution:**
1. Verify formula extraction is working correctly
2. Check OpenAI API quotas and rate limits
3. Review recent formula classification changes
4. Consider retraining AI prompts if accuracy consistently low

### Performance Issues

#### Slow Formula Extraction

**Symptoms:**
- `FormulaExtractionSlow` alert firing
- Extraction duration > 30 seconds (95th percentile)

**Resolution:**
1. Check sheet size and complexity
2. Optimize cache usage: ensure cache/normalized/ has sufficient disk space
3. Consider pagination for very large sheets
4. Review network connectivity to Google Sheets API

#### High Memory Usage

**Symptoms:**
- Service restarts due to OOM
- Slow response times

**Resolution:**
1. Monitor dependency graph sizes
2. Implement graph size limits in configuration
3. Clear old cache entries: `find cache/ -mtime +7 -delete`
4. Consider horizontal scaling for large deployments

## Deployment Procedures

### Rolling Deployment
```bash
# Deploy new version
docker-compose build construction-mcp
docker-compose up -d construction-mcp

# Monitor for 5 minutes
watch -n 30 docker-compose ps

# Check metrics
curl http://localhost:9092/api/v1/query?query=up{job="buildbridge-mcp"}
```

### Rollback Plan
```bash
# Quick rollback to previous version
docker-compose down
git checkout <previous_commit>
docker-compose build construction-mcp
docker-compose up -d

# Verify rollback success
curl http://localhost:8002/health
```

## Maintenance Tasks

### Weekly
- [ ] Review alert history in Grafana
- [ ] Check cache disk usage: `du -sh cache/`
- [ ] Verify Google Sheets API quota usage
- [ ] Update dependencies: `pip list --outdated`

### Monthly
- [ ] Archive old cache files (>30 days)
- [ ] Review and update alerting thresholds
- [ ] Test formula extraction on new sheet types
- [ ] Update AI prompts based on user feedback

### Emergency Contacts
- **Primary**: DevOps Team (devops@buildbridge.com)
- **Secondary**: AI/ML Team (ai@buildbridge.com)
- **Escalation**: CTO (cto@buildbridge.com)

## Configuration Reference

### Environment Variables
```bash
# Required
GOOGLE_SHEETS_CREDENTIALS_PATH=config/credentials.json
OPENAI_API_KEY=your_openai_key

# Optional
FORMULA_CACHE_TTL=3600
MAX_DEPENDENCY_DEPTH=10
AI_MODEL=gpt-4
LOG_LEVEL=info
```

### Key Files
- `config/credentials.json`: Google Sheets API credentials
- `deploy/prometheus/alert_rules.yml`: Alerting rules
- `cache/normalized/formulas/`: Formula extraction cache
- `logs/server.log`: Application logs

## Security Considerations

### Credentials Management
- Store Google Sheets credentials securely (not in git)
- Rotate API keys regularly
- Use environment variables for sensitive config

### Data Privacy
- Formula extraction may include sensitive business data
- Ensure proper access controls on cached data
- Implement data retention policies for cache

### Network Security
- Use HTTPS for all external API calls
- Implement rate limiting for formula extraction endpoints
- Monitor for unusual API usage patterns
