# Replit Guide

- Always read this file before making changes.
- Keep the guide up to date whenever you modify the codebase.
- The project provides a terminal-based OpenAI usage tracker (`usage_tracker.py`).
- Install dependencies with `pip install -r requirements.txt` before running tools.
- Run `python usage_tracker.py --help` to learn about live usage tracking options.
- Usage now relies on an Admin API key (`OPENAI_ADMIN_KEY`) and a project API key ID (`key_...`). The tracker calls the Organization Usage API and refreshes a sliding window each interval.
- Refreshes are capped to 600s so the tool checks usage at least every 10 minutes, and it surfaces alerts when token/request rates spike between polls. Configure thresholds with `--spike-token-rate` and `--spike-request-rate`.
- Est. cost is shown per model/total using the provided tiered pricing tables; choose the tier with `--tier` (standard by default).
