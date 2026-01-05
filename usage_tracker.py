#!/usr/bin/env python3
"""Terminal GUI for monitoring OpenAI API key usage in near real time.

This script uses the OpenAI Organization Usage API to fetch token counts
grouped by API key and model. It requires an Admin API key (managed on the
Admin Keys page) and the ID of the project API key you want to track
(key_...). Secret key values (sk-...) cannot be used directly.
"""

import argparse
import datetime as dt
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import requests
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.text import Text

COMPLETIONS_USAGE_URL = "https://api.openai.com/v1/organization/usage/completions"
console = Console()


# USD per 1M tokens per tier/model. Cached defaults to input when omitted.
COST_RATES: Dict[str, Dict[str, Tuple[float, Optional[float], Optional[float]]]] = {
    "standard": {
        "chatgpt-image-latest": (5.0, 1.25, 10.0),
        "codex-mini-latest": (1.5, 0.375, 6.0),
        "computer-use-preview": (3.0, None, 12.0),
        "gpt-4.1": (2.0, 0.5, 8.0),
        "gpt-4.1-mini": (0.4, 0.1, 1.6),
        "gpt-4.1-nano": (0.1, 0.025, 0.4),
        "gpt-4o": (2.5, 1.25, 10.0),
        "gpt-4o-2024-05-13": (5.0, None, 15.0),
        "gpt-4o-audio-preview": (2.5, None, 10.0),
        "gpt-4o-mini": (0.15, 0.075, 0.6),
        "gpt-4o-mini-audio-preview": (0.15, None, 0.6),
        "gpt-4o-mini-realtime-preview": (0.6, 0.3, 2.4),
        "gpt-4o-mini-search-preview": (0.15, None, 0.6),
        "gpt-4o-realtime-preview": (5.0, 2.5, 20.0),
        "gpt-4o-search-preview": (2.5, None, 10.0),
        "gpt-5": (1.25, 0.125, 10.0),
        "gpt-5-chat-latest": (1.25, 0.125, 10.0),
        "gpt-5-codex": (1.25, 0.125, 10.0),
        "gpt-5-mini": (0.25, 0.025, 2.0),
        "gpt-5-nano": (0.05, 0.005, 0.4),
        "gpt-5-pro": (15.0, None, 120.0),
        "gpt-5-search-api": (1.25, 0.125, 10.0),
        "gpt-5.1": (1.25, 0.125, 10.0),
        "gpt-5.1-chat-latest": (1.25, 0.125, 10.0),
        "gpt-5.1-codex": (1.25, 0.125, 10.0),
        "gpt-5.1-codex-max": (1.25, 0.125, 10.0),
        "gpt-5.1-codex-mini": (0.25, 0.025, 2.0),
        "gpt-5.2": (1.75, 0.175, 14.0),
        "gpt-5.2-chat-latest": (1.75, 0.175, 14.0),
        "gpt-5.2-pro": (21.0, None, 168.0),
        "gpt-audio": (2.5, None, 10.0),
        "gpt-audio-mini": (0.6, None, 2.4),
        "gpt-image-1": (5.0, 1.25, 0.0),
        "gpt-image-1-mini": (2.0, 0.2, 0.0),
        "gpt-image-1.5": (5.0, 1.25, 10.0),
        "gpt-realtime": (4.0, 0.4, 16.0),
        "gpt-realtime-mini": (0.6, 0.06, 2.4),
        "o1": (15.0, 7.5, 60.0),
        "o1-mini": (1.1, 0.55, 4.4),
        "o1-pro": (150.0, None, 600.0),
        "o3": (2.0, 0.5, 8.0),
        "o3-deep-research": (10.0, 2.5, 40.0),
        "o3-mini": (1.1, 0.55, 4.4),
        "o3-pro": (20.0, None, 80.0),
        "o4-mini": (1.1, 0.275, 4.4),
        "o4-mini-deep-research": (2.0, 0.5, 8.0),
    },
    "priority": {
        "gpt-4.1": (3.5, 0.875, 14.0),
        "gpt-4.1-mini": (0.7, 0.175, 2.8),
        "gpt-4.1-nano": (0.2, 0.05, 0.8),
        "gpt-4o": (4.25, 2.125, 17.0),
        "gpt-4o-2024-05-13": (8.75, None, 26.25),
        "gpt-4o-mini": (0.25, 0.125, 1.0),
        "gpt-5": (2.5, 0.25, 20.0),
        "gpt-5-mini": (0.45, 0.045, 3.6),
        "gpt-5.1": (2.5, 0.25, 20.0),
        "gpt-5.1-codex": (2.5, 0.25, 20.0),
        "gpt-5.1-codex-max": (2.5, 0.25, 20.0),
        "gpt-5.2": (3.5, 0.35, 28.0),
        "o3": (3.5, 0.875, 14.0),
        "o4-mini": (2.0, 0.5, 8.0),
    },
    "flex": {
        "gpt-5": (0.625, 0.0625, 5.0),
        "gpt-5-mini": (0.125, 0.0125, 1.0),
        "gpt-5-nano": (0.025, 0.0025, 0.2),
        "gpt-5.1": (0.625, 0.0625, 5.0),
        "gpt-5.2": (0.875, 0.0875, 7.0),
        "o3": (1.0, 0.25, 4.0),
        "o4-mini": (0.55, 0.138, 2.2),
    },
    "batch": {
        "gpt-4.1": (1.0, None, 4.0),
        "gpt-4.1-mini": (0.2, None, 0.8),
        "gpt-4.1-nano": (0.05, None, 0.2),
        "gpt-4o": (1.25, None, 5.0),
        "gpt-4o-2024-05-13": (2.5, None, 7.5),
        "gpt-4o-mini": (0.075, None, 0.3),
        "gpt-5": (0.625, 0.0625, 5.0),
        "gpt-5-mini": (0.125, 0.0125, 1.0),
        "gpt-5-nano": (0.025, 0.0025, 0.2),
        "gpt-5-pro": (7.5, None, 60.0),
        "gpt-5.1": (0.625, 0.0625, 5.0),
        "gpt-5.2": (0.875, 0.0875, 7.0),
        "gpt-5.2-pro": (10.5, None, 84.0),
        "o1": (7.5, None, 30.0),
        "o1-pro": (75.0, None, 300.0),
        "o3": (1.0, None, 4.0),
        "o3-deep-research": (5.0, None, 20.0),
        "o3-pro": (10.0, None, 40.0),
        "o4-mini": (0.55, None, 2.2),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Track OpenAI token usage for a specific project API key (key_...) "
            "using the Organization Usage API."
        ),
    )
    parser.add_argument(
        "--admin-key",
        dest="admin_key",
        help="OpenAI Admin API key. Defaults to OPENAI_ADMIN_KEY environment variable.",
    )
    parser.add_argument(
        "--api-key-id",
        dest="api_key_id",
        required=True,
        help="The project API key ID to track (looks like key_...).",
    )
    parser.add_argument(
        "--lookback-hours",
        dest="lookback_hours",
        type=int,
        default=6,
        help="How many hours of usage to include (defaults to 6).",
    )
    parser.add_argument(
        "--bucket-width",
        dest="bucket_width",
        choices=["1m", "1h", "1d"],
        default="1h",
        help="Bucket size for usage aggregation (defaults to 1h).",
    )
    parser.add_argument(
        "--tier",
        dest="tier",
        choices=sorted(COST_RATES.keys()),
        default="standard",
        help="Service tier used for cost estimation (defaults to standard).",
    )
    parser.add_argument(
        "--interval",
        dest="interval",
        type=float,
        default=15.0,
        help="Seconds between refreshes. Default: 15 seconds (max 600s).",
    )
    parser.add_argument(
        "--spike-token-rate",
        dest="spike_token_rate",
        type=float,
        default=10000.0,
        help=(
            "Token delta per minute that triggers a spike alert (defaults to 10k tokens/min)."
        ),
    )
    parser.add_argument(
        "--spike-request-rate",
        dest="spike_request_rate",
        type=float,
        default=120.0,
        help=(
            "Request delta per minute that triggers a spike alert (defaults to 120 requests/min)."
        ),
    )
    return parser.parse_args()


def resolve_admin_key(cli_key: Optional[str]) -> str:
    key = cli_key or os.getenv("OPENAI_ADMIN_KEY")
    if not key:
        console.print(
            "[red]No Admin API key supplied. Provide --admin-key or set OPENAI_ADMIN_KEY.[/red]"
        )
        sys.exit(1)
    return key


def time_window(hours: int) -> Dict[str, int]:
    if hours < 1:
        raise ValueError("lookback-hours must be at least 1")
    end_time = int(time.time())
    start_time = end_time - hours * 3600
    return {"start_time": start_time, "end_time": end_time}


def fetch_usage(
    session: requests.Session,
    admin_key: str,
    api_key_id: str,
    window: Dict[str, int],
    bucket_width: str,
) -> List[Dict]:
    headers = {
        "Authorization": f"Bearer {admin_key}",
        "Content-Type": "application/json",
    }

    params = {
        "start_time": window["start_time"],
        "end_time": window["end_time"],
        "bucket_width": bucket_width,
        "api_key_ids[]": api_key_id,
        "group_by[]": "model",
        "limit": 100,
    }

    url = COMPLETIONS_USAGE_URL
    results: List[Dict] = []
    next_page: Optional[str] = None

    while True:
        request_params = dict(params)
        if next_page:
            request_params["page"] = next_page

        response = session.get(url, headers=headers, params=request_params, timeout=20)
        if response.status_code != 200:
            raise RuntimeError(
                f"Usage request failed ({response.status_code}): {response.text}"
            )

        payload = response.json()
        results.extend(payload.get("data", payload.get("results", [])))
        next_page = payload.get("next_page")
        if not next_page:
            break

    return results


def price_lookup(model: str, tier: str) -> Optional[Tuple[float, Optional[float], Optional[float]]]:
    return COST_RATES.get(tier, {}).get(model)


def estimate_cost(
    model: str,
    tier: str,
    input_tokens: int,
    cached_tokens: int,
    output_tokens: int,
) -> Optional[float]:
    rates = price_lookup(model, tier)
    if not rates:
        return None

    input_rate, cached_rate, output_rate = rates
    effective_cached_rate = cached_rate if cached_rate is not None else input_rate
    effective_output_rate = output_rate if output_rate is not None else 0.0

    input_billable = max(input_tokens - cached_tokens, 0)
    cached_billable = cached_tokens

    cost = (
        input_billable * input_rate
        + cached_billable * effective_cached_rate
        + output_tokens * effective_output_rate
    ) / 1_000_000
    return cost


def summarize_usage(data_rows: List[Dict], tier: str) -> Dict:
    totals = {
        "input": 0,
        "output": 0,
        "cached_input": 0,
        "requests": 0,
        "cost": 0.0,
    }
    rows: List[Dict] = []

    for entry in data_rows:
        model = entry.get("model") or entry.get("group", "unknown")
        input_tokens = int(entry.get("input_tokens", entry.get("n_input_tokens", 0)))
        output_tokens = int(entry.get("output_tokens", entry.get("n_output_tokens", 0)))
        cached_tokens = int(
            entry.get("cached_input_tokens", entry.get("n_cached_input_tokens", 0))
        )
        request_count = int(
            entry.get("num_model_requests")
            or entry.get("n_requests", 0)
            or entry.get("n_model_requests", 0)
        )

        cost = estimate_cost(
            model,
            tier,
            input_tokens=input_tokens,
            cached_tokens=cached_tokens,
            output_tokens=output_tokens,
        )

        rows.append(
            {
                "model": model,
                "input": input_tokens,
                "output": output_tokens,
                "cached": cached_tokens,
                "requests": request_count,
                "cost": cost,
            }
        )

        totals["input"] += input_tokens
        totals["output"] += output_tokens
        totals["cached_input"] += cached_tokens
        totals["requests"] += request_count
        if cost is not None:
            totals["cost"] += cost

    totals["total_tokens"] = totals["input"] + totals["output"]
    return {"totals": totals, "rows": rows}


def render_usage(
    summary: Dict,
    window: Dict[str, int],
    api_key_id: str,
    tier: str,
    alerts: Optional[List[str]] = None,
) -> Group:
    table = Table(title="OpenAI API Key Usage", title_style="bold cyan")
    table.add_column("Model", justify="left")
    table.add_column("Input", justify="right")
    table.add_column("Output", justify="right")
    table.add_column("Cached", justify="right")
    table.add_column("Requests", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Est Cost ($)", justify="right")

    totals = summary["totals"]
    rows = summary["rows"]

    for row in rows:
        total_tokens = row["input"] + row["output"]
        cost_display = f"${row['cost']:.4f}" if row["cost"] is not None else "—"
        table.add_row(
            row["model"],
            f"{row['input']:,}",
            f"{row['output']:,}",
            f"{row['cached']:,}",
            f"{row['requests']:,}",
            f"{total_tokens:,}",
            cost_display,
        )

    table.add_section()
    table.add_row(
        Text("TOTAL", style="bold"),
        Text(f"{totals['input']:,}", style="bold"),
        Text(f"{totals['output']:,}", style="bold"),
        Text(f"{totals['cached_input']:,}", style="bold"),
        Text(f"{totals['requests']:,}", style="bold"),
        Text(f"{totals['total_tokens']:,}", style="bold"),
        Text(f"${totals['cost']:.4f}", style="bold"),
    )

    start = dt.datetime.utcfromtimestamp(window["start_time"]).isoformat()
    end = dt.datetime.utcfromtimestamp(window["end_time"]).isoformat()
    window_note = f"Window (UTC): {start} → {end} | API key ID: {api_key_id} | Tier: {tier}"
    table.caption = f"{window_note}  |  Cached counts are a subset of input tokens."
    alert_renderables: List[Text] = []
    for alert in alerts or []:
        alert_renderables.append(Text.from_markup(f"[bold yellow]Alert:[/bold yellow] {alert}"))

    if alert_renderables:
        return Group(*alert_renderables, table)

    return Group(table)


def render_error(message: str) -> Text:
    return Text.from_markup(f"[bold red]Error:[/bold red] {message}")


def clamp_interval(interval: float) -> float:
    """Ensure the refresh interval checks usage at least every 10 minutes."""

    max_interval = 600.0
    if interval > max_interval:
        console.print(
            f"[yellow]Interval capped at 600s to check usage at least every 10 minutes (requested {interval}s).[/yellow]"
        )
        return max_interval
    return interval


def detect_spikes(
    prev_totals: Optional[Dict[str, int]],
    current_totals: Dict[str, int],
    interval_seconds: float,
    token_rate_threshold: float,
    request_rate_threshold: float,
) -> List[str]:
    if not prev_totals:
        return []

    elapsed_minutes = max(interval_seconds / 60.0, 1e-6)
    delta_tokens = current_totals["total_tokens"] - prev_totals.get("total_tokens", 0)
    delta_requests = current_totals["requests"] - prev_totals.get("requests", 0)

    token_rate = delta_tokens / elapsed_minutes
    request_rate = delta_requests / elapsed_minutes

    alerts: List[str] = []
    if token_rate >= token_rate_threshold:
        alerts.append(
            f"Token spike: {delta_tokens:,} tokens since last check (~{token_rate:,.0f}/min)."
        )
    if request_rate >= request_rate_threshold:
        alerts.append(
            f"Request spike: {delta_requests:,} requests since last check (~{request_rate:,.0f}/min)."
        )

    return alerts


def main() -> None:
    args = parse_args()
    admin_key = resolve_admin_key(args.admin_key)
    interval = clamp_interval(args.interval)
    session = requests.Session()

    console.print(
        "Tracking usage for [bold]OpenAI project API key[/bold] "
        f"[magenta]{args.api_key_id}[/magenta] (refresh {interval}s) on tier [cyan]{args.tier}[/cyan]."
    )
    console.print("Press Ctrl+C to exit.\n")

    prev_totals: Optional[Dict[str, int]] = None

    with Live(console=console, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                try:
                    window = time_window(args.lookback_hours)
                    usage_rows = fetch_usage(
                        session,
                        admin_key=admin_key,
                        api_key_id=args.api_key_id,
                        window=window,
                        bucket_width=args.bucket_width,
                    )
                    summary = summarize_usage(usage_rows, tier=args.tier)
                    alerts = detect_spikes(
                        prev_totals,
                        summary["totals"],
                        interval_seconds=interval,
                        token_rate_threshold=args.spike_token_rate,
                        request_rate_threshold=args.spike_request_rate,
                    )
                    prev_totals = summary["totals"]
                    live.update(
                        render_usage(
                            summary,
                            window,
                            args.api_key_id,
                            tier=args.tier,
                            alerts=alerts,
                        )
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    live.update(render_error(str(exc)))
                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Stopping tracker.[/bold yellow]")


if __name__ == "__main__":
    main()
