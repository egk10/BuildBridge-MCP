# Week 4 GPT-5 Codex Implementation Plan

## Goals
- Increase response accuracy and reliability for BuildBridge-MCP queries.
- Introduce guardrails that validate data and AI outputs before delivery.
- Lay the groundwork for local LLM/SLM adoption without disrupting production.

## Guiding Principles
- Ship in tight, reviewable increments that leave the system in a releasable state.
- Prioritize data correctness before downstream AI improvements.
- Instrument everything we change with observable metrics and automated checks.
- Keep fallbacks for every new feature to avoid regressions during rollout.

## Iteration Overview
Each iteration ends with a go/no-go review. The "Next focus" field captures what to tackle immediately after the iteration succeeds.

| Iteration | Priority | Focus | Key Deliverables | Exit Criteria | Next Focus |
|-----------|----------|-------|------------------|---------------|------------|
| I1 | P0 | Data validation & normalization | nightly validation job, normalized registry cache, provenance tagging | All connectors produce a validated normalized dataset; alerts fire on contract violations | Move to accuracy harness work (I2) |
| I2 | P0 | Accuracy harness & regression suite | gold query set, automated response evaluator, CI gate | Harness passes on current prod provider; CI blocks <95% accuracy on gold set | Instrument monitoring/metrics (I3) |
| I3 | P1 | Observability & alerting | Prometheus counters, `/health` metrics expansion, alert hooks | Metrics expose data freshness, query volume, fallback counts; alerts verified via test fire drill | Security hardening (I4) |
| I4 | P1 | Security & access controls | JWT/OAuth guards, secret storage updates, sensitive log scrubbing | Auth required for API access; secrets encrypted; logs sanitized | AI provider abstraction (I5) |
| I5 | P2 | AI provider abstraction | provider interface, config switch, OpenAI + placeholder local provider | Integration tests pass for both providers; failover path exercised | Local LLM pilot (I6) |
| I6 | P2 | Local LLM/SLM pilot | Ollama/vLLM setup, fine-tune recipe, dual-provider evaluation dashboard | Local model meets or exceeds defined accuracy threshold; rollout plan approved | Plan for production rollout & monitoring refinement |

## Iteration Details

### Iteration I1 — Data Validation & Normalization (Priority P0)
- **Current data flow map (inventory for validation rules)**
  - **Excel connector** (`ExcelConnector`)
    - *Entry points*: `get_project_data`, `get_budget_data`, `get_schedule_data`, `get_resource_data` → all call `read_excel_file(file_type)` which pulls from `config['excel_files']`.
    - *Expected identifiers*: looks for `ProjectID`, `ID`, `Project_ID`, or `project_id` when filtering; schedules/resources also accept `Project`.
    - *Key fields in wild*: budget sheet expects `BudgetAllocated`, `BudgetSpent` to compute variance; schedules check `PlannedEndDate`, `ActualEndDate` for delays.
    - *Fallbacks*: `local_mode` bypasses Graph auth and reads sample CSV/Excel from `data/sample`. Cached per `file_type` + sheet.
  - **Google Sheets connector** (`GoogleSheetsConnector`)
    - *Entry points*: similar helpers returning DataFrames from sheet configs in `config['google_sheets']` (projects.<key>, budgets, schedules, resources).
    - *Extraction quirks*: `get_project_data` parses semi structured summary sheets via `_extract_project_info_from_sheet`; it synthesizes defaults (`Status`, `Progress_Percent`, etc.) when fields missing.
    - *Expected identifiers*: merge helpers expect `ProjectID` for joins; budgets/schedules/resources filter on canonical id columns list.
    - *Fallbacks*: `local_mode` (no credentials) returns empty DataFrame; caching keyed by `sheet_id + range` for 15 min.
  - **SharePoint connector** (`SharePointConnector`)
    - *Entry points*: `get_projects_list`, `get_tasks_list`, `get_safety_incidents`, `get_subcontractors` using configured list names; data returned as dicts.
    - *Expected identifiers*: filters rely on `ProjectID` or list-specific fields (`IncidentDate`, `Status`). Schema discovery reads list metadata via `get_list_schema`.
    - *Fallbacks*: local mode yields empty list; otherwise caches responses for 15 min.
  - **Schema discovery** (`SchemaDiscovery`)
    - Harmonizes columns to standard names per data type (`projects`, `budgets`, `schedules`, `resources`). Infers types, caches JSON in `cache/schemas`.
    - Provides `validate_data_against_schema` but required flags mostly inherit SharePoint metadata; Excel/Sheets rely on inferred types.
- **Objectives**
  - Define data contracts per connector (required columns, types, freshness windows).
  - Implement nightly (or on-demand) validation script that loads each data source, checks contracts, and writes results.
  - Generate a `projects_normalized.json` (or parquet) cache with provenance metadata (source, refresh timestamp).
- **Tasks**
  - Draft schema definitions and guard clauses inside `schema_discovery.py`.
  - Add validation CLI (`scripts/validate_data.py`) and integrate with cron/GitHub Action.
  - Update connectors to emit provenance tags and use normalized cache when available.
  - Document remediation procedure for validation failures.
- **Risks & Mitigations**
  - *Connector downtime*: keep existing live pathway as fallback if cache missing.
  - *Schema drift*: maintain per-source contract files versioned in `config/contracts/`.
- **Exit Review Checklist**
  - Validation job succeeds end-to-end on sample data.
  - Alert/notification triggers when intentionally breaking a contract.
  - MCP query path can consume cached normalized data without regressions.
  - Decision: green-light Iteration I2.

### Iteration I2 — Accuracy Harness & Regression Suite (Priority P0)
- **Objectives**
  - Build a gold Q&A dataset representing critical user journeys.
  - Automate response checks via CLI and CI (call `/process` or `ConstructionMCPClient`).
  - Define accuracy budget (e.g., ≥95% match) and block merges that regress.
- **Tasks**
  - Curate dataset from `data/construction_conversation_dataset.jsonl` + new scenarios.
  - Implement deterministic evaluators (exact match for numeric fields, tolerance-based for budgets, regex for text fields).
  - Integrate with CI and document local execution instructions.
- **Risks & Mitigations**
  - *LLM variability*: use deterministic prompts + temperature=0; fallback to template-based responses on validation failure.
  - *Dataset bias*: review with SME stakeholders before locking thresholds.
- **Exit Review Checklist**
  - Harness passes against current OpenAI provider.
  - CI fails on simulated regression and passes once fixed.
  - Stakeholders approve gold dataset coverage.
  - Decision: proceed to Iteration I3.

### Iteration I3 — Observability & Alerting (Priority P1)
- **Objectives**
  - Provide visibility into data freshness, query load, validation failures, and fallback rates.
  - Expose metrics via Prometheus and enhance `/health` endpoint.
  - Set up alerting pathways (Slack/email) for critical events.
- **Tasks**
  - Instrument connectors and `production_mcp_integration.py` with counters/gauges.
  - Expand `/health` to return structured metrics summary.
  - Configure Prometheus scrape targets and alert rules; smoke-test notifications.
- **Risks & Mitigations**
  - *Metric overhead*: use sampling or caching to keep cost low.
  - *Alert fatigue*: define clear severity levels and escalation paths.
- **Exit Review Checklist**
  - Metrics visible in Grafana dashboard (aggregation node via OPI5 if desired).
  - Test alert fires and is acknowledged.
  - Operators can trace validation or accuracy failures through dashboards.
  - Decision: advance to security hardening (I4).

### Iteration I4 — Security & Access Controls (Priority P1)
- **Objectives**
  - Enforce authenticated access to MPC endpoints and WebSocket streams.
  - Protect secrets and sensitive data at rest and in transit.
  - Ensure logging excludes confidential fields.
- **Tasks**
  - Implement JWT/OAuth2 guard in FastAPI layer with role scopes.
  - Encrypt cached tokens/credentials; rotate keys via `config/` processes.
  - Add log filters/masking for PII or sensitive budgets.
  - Update documentation for credential provisioning and rotation cadence.
- **Risks & Mitigations**
  - *Operational friction*: provide tooling (scripts) to issue tokens and manage roles.
  - *Backward compatibility*: maintain local dev bypass flag for tests.
- **Exit Review Checklist**
  - Auth enforced in staging; manual pen-test passes basic checks.
  - Logs audited to confirm masking.
  - On-call runbook updated with auth troubleshooting steps.
  - Decision: move to AI provider abstraction (I5).

### Iteration I5 — AI Provider Abstraction (Priority P2)
- **Objectives**
  - Decouple `AIService` from any single provider.
  - Support configuration-based selection between OpenAI and local providers.
  - Implement graceful failover and fallback logic.
- **Tasks**
  - Define provider interface (prompt formatting, completion call, cost metrics).
  - Refactor existing OpenAI implementation to conform to interface.
  - Add placeholder local provider stub (e.g., HTTP call to Ollama/vLLM).
  - Extend accuracy harness to run against multiple providers.
- **Risks & Mitigations**
  - *Interface churn*: write contract tests per provider.
  - *Latency differences*: include timeout handling and fallback to deterministic templates.
- **Exit Review Checklist**
  - Both providers selectable via config; integration tests pass.
  - Failover path demonstrated during review.
  - Documentation updated with provider onboarding guide.
  - Decision: begin local LLM pilot (I6).

### Iteration I6 — Local LLM/SLM Pilot (Priority P2)
- **Objectives**
  - Stand up local inference stack (Ollama/vLLM) on homelab hardware.
  - Fine-tune or calibrate selected model with construction domain data.
  - Compare local provider performance vs OpenAI across metrics (accuracy, latency, cost, privacy).
- **Tasks**
  - Provision GPU node via Tailscale, install inference runtime, set access controls.
  - Prepare training/eval datasets; run LoRA fine-tuning if needed.
  - Extend dashboards to display provider comparison metrics.
  - Draft rollout plan including fallback and rollback procedures.
- **Risks & Mitigations**
  - *Hardware constraints*: start with quantized 8B models; monitor resource usage.
  - *Accuracy gaps*: iterate on fine-tuning, prompt engineering, or hybrid responses.
- **Exit Review Checklist**
  - Local provider meets agreed accuracy threshold on harness.
  - Latency acceptable for user experience.
  - Stakeholders sign off on privacy/compliance requirements.
  - Decision: execute production rollout plan & enter continuous improvement cycle.

## Supporting Backlog
- Build reconciliation logic when multiple sources disagree on the same field.
- Add structured citation metadata to AI responses for audit trails.
- Automate Ceph backups of normalized datasets and model artifacts.
- Expand Grafana dashboard with cluster and LLM performance widgets.
- Develop chaos tests (connector downtime, provider outages) to validate resiliency.

## Review Cadence
- Run iteration review at the end of each sprint or completion milestone.
- Update this plan with lessons learned, re-prioritizing backlog items as needed.
- Track progress in `TESTING_SUMMARY.md` or a dedicated status log for transparency.
