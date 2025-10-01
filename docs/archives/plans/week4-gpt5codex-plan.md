# Week 4 GPT-5 Codex Plan

## Conversation Overview
- **Primary objectives**
  - Deliver a holistic architecture analysis for the BuildBridge-MCP stack.
  - Recommend improvements to make responses cleaner, more reliable, and more accurate.
  - Evaluate the feasibility of running a local LLM/SLM for privacy-focused deployments.
- **Engagement flow**
  - Audited documentation and core modules to understand the current design.
  - Produced architectural recommendations covering validation, monitoring, and security.
  - Assessed strategies for local model adoption to complement or replace cloud AI providers.

## Technical Foundation
- BuildBridge-MCP is a Python-based MCP server with FastAPI for production deployment.
- Connectors support Excel/OneDrive, SharePoint lists, and document repositories.
- `AIService` (OpenAI-backed) orchestrates prompts from `construction_prompts.py`.
- Schema discovery normalizes heterogeneous data fields before answering queries.

## Codebase Status
- **`production_mcp_integration.py`** handles the production FastAPI + WebSocket API via `ConstructionMCPEngine`, `/process` inference endpoint, log streaming, and helpers.
- **`main.py`** bootstraps the MCP server, registers connectors, and defines protocol tools.
- **`config/credentials.json.template`** outlines credential and provider configuration requirements.
- No direct code edits were made during the review; activity was read-only.

## Recommendations Delivered
1. **Data validation & normalization** – Enforce schema checks before queries reach the AI layer to reduce hallucinations.
2. **Accuracy harness & monitoring** – Implement automated test suites, logging, and alerting for AI responses.
3. **Security hardening** – Protect credentials, tighten network exposure, and audit logging.
4. **Provider abstraction** – Decouple AI backends to enable seamless switching between OpenAI, local LLMs/SLMs, and future providers.
5. **Local LLM strategy** – Pilot high-quality SLMs for sensitive workflows, supported by the above safeguards.

## Pending Work & Next Steps
- Build the validation pipeline and integrate with connectors and schema discovery.
- Ship the accuracy harness with regression tests and response QA dashboards.
- Implement monitoring/alerting plus security policies before production rollout.
- Develop the AI provider abstraction layer to enable local model deployment.
- After the above, prototype local LLM/SLM hosting and measure accuracy vs. cost/privacy gains.

## Recent Operations Context
- Latest file inspections: `production_mcp_integration.py`, `main.py`, and `config/credentials.json.template` to confirm implementation details.
- Purpose of inspections: align recommendations with existing FastAPI endpoints, MCP initialization, and credential structures.
- Outputs were informational only; no modifications were applied.


🧱 Architecture at a glance
Core server (main.py) bootstraps connectors for Excel/OneDrive, SharePoint, Google Sheets, and document search, then exposes MCP tools (search, status, budget, schedule, reports).
Connectors
excel_connector.py and sharepoint_connector.py pull structured data via Microsoft Graph (with a local_mode for sample files).
google_sheets_connector.py supports both OAuth and service accounts, with caching and schema-aware extraction from real project spreadsheets.
document_indexer.py builds a keyword index across SharePoint and local files.
Schema layer (schema_discovery.py) normalizes each data source so the downstream logic doesn’t rely on rigid column names.
Query brain (query_processor.py) detects intent, routes to the right connector(s), de-duplicates, formats responses, and enriches static answers with construction context.
AI service (ai_service.py) wraps OpenAI (GPT‑4 Turbo default), tracks tokens/cost, and injects domain prompts from construction_prompts.py.
Production edge (production_mcp_integration.py) assembles everything into a FastAPI app with REST + WebSocket, detailed logging, /process AI endpoint, and a direct Python client (ConstructionMCPClient).
Docs (PROJECT_PLAN, WEEK_3-4 plan, PRODUCTION_GUIDE, etc.) lay out the roadmap: Phase 1 (external AI) ✅, Phase 2 (multi-source routing, security, monitoring) underway, later phases targeting predictive analytics and enterprise security.
💪 Strengths already in place
Modular connectors that tolerate missing services thanks to local_mode and graceful fallbacks.
Schema discovery + query normalization already reduce brittle hard-coding.
Comprehensive AI prompt guide with explicit “don’t hallucinate” rules and data-context formatting.
Production FastAPI layer handles REST/WebSockets, structured logging, live log streaming, and token-cost accounting.
Rich documentation: setup, integration comparisons, project plans, Google OAuth walkthrough.
⚠️ Gaps that keep answers noisy or fragile
Data fidelity checks – connectors trust sheet/tab layouts; if a sheet changes, the AI may see stale or partial fields (e.g., Lakeside client mismatch).
End-to-end accuracy tests – no automated suite that replays real queries and compares answers to ground truth.
Prompt/response evaluation – construction_prompts encode rules, but there’s no scoring to catch regressions when prompts or data shift.
Observability – logs exist, yet no structured metrics to prove coverage (how many projects loaded, how often fallbacks fire, etc.).
Access control – JWT/RBAC planned but not implemented; anyone hitting the API sees sensitive project data.
Data governance – connectors pull from multiple sources without reconciliation (no authoritativeness ranking or conflict resolution).
AI fallback path – when OpenAI fails, the user gets a generic apology; there’s no deterministic backup answer.
🛠️ Recommendations for cleaner, reliable, accurate responses
Data hygiene & validation
Build a nightly “data contract” check that loads each connector, validates required fields (Project_Name, client, budget, units, etc.), and raises alerts if anything is missing or suspicious.
Store a normalized registry (e.g., projects_normalized.json) that the AI service can trust, rather than re-scraping on every query.
Add provenance tags (source, last_refresh) so AI responses can cite the freshest data.
Accuracy harness
Assemble a gold-standard evaluation set (queries + expected answers) in tests/test_ai_responses.jsonl.
Add a test script test_response_accuracy.py that runs through /process (or the Python client) and diffs AI answers against expected strings/tables.
Gate deployments on the accuracy harness: no release if accuracy drops below a threshold for key projects.
Prompt & inference safeguards
Before calling OpenAI, compute the “contract” for that query: list the fields you expect in the answer (client, units, levels, etc.) and pass that explicitly in the prompt.
After receiving the response, run a validator: ensure every mandatory field is mentioned; if not, trigger a template-based answer derived directly from the normalized data.
Store prompt & response metadata (query type, tokens, data context IDs) in a small SQLite/Parquet log for auditing.
Monitoring & alerts
Extend /health to expose counts (projects loaded per source, last refresh timestamps, number of cached sheets).
Add Prometheus counters: queries per type, AI vs fallback usage, validation failures, connector errors.
Hook Slack/email alerts when: (a) data validation fails, (b) accuracy harness fails, (c) AI cost exceeds budget.
Security & privacy
Implement JWT/OAuth2 fastapi.security guard with role-based scopes (view vs admin).
Encrypt cached files (schema cache, token pickles) at rest; rotate Google OAuth tokens on schedule.
Mask sensitive fields (client contact info, budgets) before logging.
🧠 Local LLM / SLM strategy for privacy
Why local?
You said privacy is key and the roadmap already targets “local LLM foundation” (Ollama). Running inference on-site keeps project data off external APIs and lets you fine-tune domain responses.

Model size

For summary/reporting tasks with structured context, a good Small Language Model (SLM) in the 7‑13B range suffices (e.g., Llama‑3.1 8B Instruct, Mistral 7B, Phi‑3.5).
If you plan to generate long executive reports or integrate unstructured docs, stepping up to a 12‑13B model helps. Larger 34B+ models need serious GPU/RAM.
Hardware

CPU-only nodes can run quantized 4-bit models but may be slow (>10s per response).
A local GPU (RTX 4090 / A6000 class) with 24GB VRAM can host Llama‑3 8B or Mixtral 8x7B comfortably.
For homelab servers (notebook mention Ceph/Tailscale) consider a dedicated inference node with NVidia GPU or a multi-GPU server.
Integration plan

Abstract the AI client: wrap ai_service so providers become plug-ins (OpenAI, local-Ollama, local-Transformers).
Install Ollama or vLLM on the target server; expose it via HTTP (Ollama’s REST).
Quantize/fine-tune:
Start with base instruct model.
Fine-tune on your construction Q&A dataset (data/construction_conversation_dataset.jsonl).
Use LoRA or PEFT to keep GPU memory manageable.
Feature flag gradual rollout: AI_PROVIDER=openai|ollama. Begin by routing non-critical queries to the local model while still capturing accuracy metrics.
Safety nets:
Keep external GPT as fallback until the local model meets accuracy thresholds.
Run the same accuracy harness daily across both providers to compare results.
Security:
Lock the inference port behind Tailscale ACLs.
Store models on Ceph so you have redundancy and quick rollback.
When local might fall short

Heavy natural-language reasoning or long context windows (e.g., ingesting 100-page specs) may still benefit from external GPT‑4 or Azure OpenAI. Hybrid mode (local for routine, cloud for heavy) gives best of both worlds.
✅ Suggested next steps
Stand up the data validation + normalization pipeline (scripts + nightly job).
Create the accuracy harness and hook it into CI (GitHub Actions or your homelab runner).
Instrument metrics/alerts; expand /health to show data coverage.
Harden security (JWT auth, encrypted caches).
Abstract the AI provider interface so switching to local LLM becomes a config change.
Pilot Ollama with a quantized Llama‑3 8B on a dev box, run evaluations against your gold queries, and iterate on prompt/finetune until accuracy matches or exceeds OpenAI.
🔍 Quality gates
Not run — analysis only this turn; no code changes to validate.

📌 Requirements coverage
Holistic architecture & goal analysis ⇒ Done
Suggestions for clean, reliable, accurate AI responses ⇒ Done
Evaluate local LLM/SLM path for privacy ⇒ Done