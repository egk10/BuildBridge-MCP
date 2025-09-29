# Formula Awareness Runbook (Scaffolding)

This document outlines the operational steps that will accompany the
formula awareness initiative. Content will be iteratively expanded as
features are implemented.

## Pilot Extraction Workflow
- [ ] Identify pilot Google Sheets and confirm access credentials
- [ ] Run the extraction script to populate normalized cache entries
- [ ] Review generated dependency graphs and formula classifications

## Monitoring & Alerts
- [ ] Wire `formula-metrics.yml` into the Prometheus scrape config
- [ ] Define alert thresholds for extraction failures and circular references
- [ ] Verify metrics surface correctly in Grafana dashboards

## Rollback Strategy
- [ ] Document steps to disable enhanced connector in configuration
- [ ] Preserve cached baseline values for fallback
- [ ] Provide communication script for stakeholders if rollback needed

## Escalation & Support
- Primary SME: _TBD_
- Backup SME: _TBD_
- Slack channel / Pager: _TBD_
