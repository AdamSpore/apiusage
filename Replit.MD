# Replit Guide

- Always read this file before making changes.
- Keep the guide up to date whenever you modify the codebase.
- The project provides a terminal-based OpenAI usage tracker (`usage_tracker.py`) and a no-Terminal Tk GUI (`gui_usage_tracker.py`).
- Install dependencies with `pip install -r requirements.txt` before running tools.
- Run `python usage_tracker.py --help` (or `python gui_usage_tracker.py --help`) to learn about live usage tracking options.
- Usage now relies on an Admin API key (`OPENAI_ADMIN_KEY`) and a project API key ID (`key_...`). The tracker calls the Organization Usage API and refreshes a sliding window each interval.
- Refreshes are capped to 600s so the tool checks usage at least every 10 minutes, and it surfaces alerts when token/request rates spike between polls. Configure thresholds with `--spike-token-rate` and `--spike-request-rate`.
- Est. cost is shown per model/total using the provided tiered pricing tables; choose the tier with `--tier` (standard by default).
- Credentials can be supplied via `OPENAI_ADMIN_KEY` and `OPENAI_API_KEY_ID` env vars (including a local `.env` file) so the tracker or the macOS app can launch without CLI flags.
- Run `./scripts/build_installer.sh` on macOS to create both `dist/UsageTracker.app` and `dist/UsageTracker.dmg` in one step (wraps the create/package scripts). Double-click the DMG, drag `UsageTracker.app` to Applications, place a `.env` next to it, and open—no terminal needed after the DMG is built.
