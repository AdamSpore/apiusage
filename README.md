# OpenAI API Usage Tracker

A terminal-based GUI for monitoring OpenAI project API key usage in near real time. The tracker queries the Organization Usage API and shows token totals per model for a specific key ID (key_...).

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Obtain an **Admin API key** (only org owners can create these) and export it as `OPENAI_ADMIN_KEY` or pass it via `--admin-key`.
3. Locate the project API key **ID** you want to track (looks like `key_...`). You can list project keys with:
   ```bash
   curl "https://api.openai.com/v1/organization/projects/<proj_id>/api_keys?limit=100" \
     -H "Authorization: Bearer $OPENAI_ADMIN_KEY" \
     -H "Content-Type: application/json"
   ```
   Use `data[].id` from the response.

## Usage
Run the tracker from your terminal:
```bash
python usage_tracker.py --api-key-id key_ABC123
```

Launch the no-Terminal GUI (Tk window) instead:
```bash
python gui_usage_tracker.py
```

You can also place your credentials in a local `.env` file so the CLI/app can read them automatically:
```bash
OPENAI_ADMIN_KEY=key_admin_...
OPENAI_API_KEY_ID=key_ABC123
```

Useful options:
- `--lookback-hours`: Hours of usage to include (default: 6).
- `--bucket-width`: Aggregation bucket (`1m`, `1h`, or `1d`; default: `1h`).
- `--tier`: Service tier used for cost estimation (choices: batch, flex, priority, standard; default: standard).
- `--interval`: Seconds between refreshes (default: 15; capped at 600s to ensure checks at least every 10 minutes).
- `--admin-key`: Override `OPENAI_ADMIN_KEY` at runtime.
- `--spike-token-rate`: Token delta per minute that triggers a spike alert (default: 10k tokens/min).
- `--spike-request-rate`: Request delta per minute that triggers a spike alert (default: 120 requests/min).

Press `Ctrl+C` to exit the live view. The display shows per-model input, output, cached input tokens, request counts, totals, and an estimated cost based on the selected tier/model pricing tables above. The window updates on each refresh to keep the view current, and will surface in-line alerts when token or request rates spike between refreshes.

## macOS double-click app (no Terminal)
If you just want an installer you can build once and then open like any other Mac app:

1. Make sure Python 3 is installed on your Mac and install dependencies once:
   ```bash
   pip install -r requirements.txt
   ```
2. Populate a `.env` file in the repository folder with your credentials so the app can launch without prompts:
   ```bash
   OPENAI_ADMIN_KEY=key_admin_...
   OPENAI_API_KEY_ID=key_ABC123
   ```
3. Build the double-clickable app **and** DMG installer in one command (macOS only):
   ```bash
   ./scripts/build_installer.sh
   ```
   This wraps the existing `create_mac_app.sh` and `package_mac_app.sh` steps and leaves you with `dist/UsageTracker.app` plus `dist/UsageTracker.dmg`.
4. Open `dist/UsageTracker.dmg` and drag `UsageTracker.app` into Applications.
5. Ensure a `.env` (or the included `.env.example` renamed to `.env`) lives next to the app or in the same folder you launch it from so the GUI can read `OPENAI_ADMIN_KEY` and `OPENAI_API_KEY_ID` automatically.
6. Double-click `UsageTracker.app` from Applications. The GUI opens and starts polling usage with the credentials from `.env`; no terminal needed after the DMG is built.
