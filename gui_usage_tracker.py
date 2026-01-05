#!/usr/bin/env python3
"""Tkinter window for monitoring OpenAI API key usage without Terminal.

This GUI reuses the Organization Usage API polling logic from `usage_tracker.py`
so a macOS app bundle can launch it directly. It shows per-model token counts,
requests, and estimated costs with optional spike alerts.
"""
import argparse
import datetime as dt
import threading
import tkinter as tk
from tkinter import ttk
from typing import List, Optional

import requests

import usage_tracker


class UsageTrackerGUI:
    """Tkinter-based viewer for the usage tracker."""

    def __init__(self, args: argparse.Namespace):
        usage_tracker.load_env_file()
        self.admin_key = usage_tracker.resolve_admin_key(args.admin_key)
        self.api_key_id = usage_tracker.resolve_api_key_id(args.api_key_id)
        self.lookback_hours = args.lookback_hours
        self.bucket_width = args.bucket_width
        self.tier = args.tier
        self.interval = usage_tracker.clamp_interval(args.interval)
        self.spike_token_rate = args.spike_token_rate
        self.spike_request_rate = args.spike_request_rate

        self.session = requests.Session()
        self.prev_totals: Optional[dict] = None
        self._refresh_inflight = False

        self.root = tk.Tk()
        self.root.title("OpenAI Usage Tracker")
        self.root.geometry(args.geometry)

        header = ttk.Label(
            self.root,
            text="OpenAI API Key Usage",
            font=("SF Pro", 16, "bold"),
        )
        header.pack(pady=(10, 4))

        subtitle = ttk.Label(
            self.root,
            text=(
                f"API Key ID: {self.api_key_id}  |  Tier: {self.tier}  |  "
                f"Refresh: {self.interval:.0f}s"
            ),
        )
        subtitle.pack(pady=(0, 8))

        columns = (
            "model",
            "input",
            "output",
            "cached",
            "requests",
            "total",
            "cost",
        )
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=12)
        headings = {
            "model": "Model",
            "input": "Input",
            "output": "Output",
            "cached": "Cached",
            "requests": "Requests",
            "total": "Total",
            "cost": "Est Cost ($)",
        }
        widths = {
            "model": 200,
            "input": 120,
            "output": 120,
            "cached": 120,
            "requests": 120,
            "total": 120,
            "cost": 120,
        }
        for key in columns:
            self.tree.heading(key, text=headings[key])
            self.tree.column(key, width=widths[key], anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=12)

        self.alert_var = tk.StringVar()
        self.alert_label = ttk.Label(
            self.root, textvariable=self.alert_var, foreground="#d97706"
        )
        self.alert_label.pack(pady=(8, 0))

        self.status_var = tk.StringVar(value="Loading usage…")
        status = ttk.Label(self.root, textvariable=self.status_var)
        status.pack(pady=(4, 10))

        self.schedule_refresh(initial=True)
        self.root.protocol("WM_DELETE_WINDOW", self.root.quit)

    def schedule_refresh(self, initial: bool = False) -> None:
        if self._refresh_inflight:
            return
        self._refresh_inflight = True
        thread = threading.Thread(target=self._refresh_once, daemon=True)
        thread.start()
        if not initial:
            self.root.after(int(self.interval * 1000), self.schedule_refresh)

    def _refresh_once(self) -> None:
        try:
            window = usage_tracker.time_window(self.lookback_hours)
            usage_rows = usage_tracker.fetch_usage(
                self.session,
                admin_key=self.admin_key,
                api_key_id=self.api_key_id,
                window=window,
                bucket_width=self.bucket_width,
            )
            summary = usage_tracker.summarize_usage(usage_rows, tier=self.tier)
            alerts = usage_tracker.detect_spikes(
                self.prev_totals,
                summary["totals"],
                interval_seconds=self.interval,
                token_rate_threshold=self.spike_token_rate,
                request_rate_threshold=self.spike_request_rate,
            )
            self.prev_totals = summary["totals"]
            self.root.after(0, self._update_ui, summary, window, alerts)
        except Exception as exc:  # pylint: disable=broad-except
            self.root.after(0, self.show_error, str(exc))
        finally:
            if not self.root.winfo_exists():
                return
            self._refresh_inflight = False
            self.root.after(int(self.interval * 1000), self.schedule_refresh)

    def _update_ui(self, summary: dict, window: dict, alerts: List[str]) -> None:
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        for row in summary["rows"]:
            total_tokens = row["input"] + row["output"]
            cost_display = f"${row['cost']:.4f}" if row["cost"] is not None else "—"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    row["model"],
                    f"{row['input']:,}",
                    f"{row['output']:,}",
                    f"{row['cached']:,}",
                    f"{row['requests']:,}",
                    f"{total_tokens:,}",
                    cost_display,
                ),
            )

        totals = summary["totals"]
        cost_display = f"${totals['cost']:.4f}"
        start = dt.datetime.utcfromtimestamp(window["start_time"]).strftime("%Y-%m-%d %H:%M")
        end = dt.datetime.utcfromtimestamp(window["end_time"]).strftime("%Y-%m-%d %H:%M")
        self.status_var.set(
            " | ".join(
                [
                    f"Window (UTC): {start} → {end}",
                    f"Total tokens: {totals['total_tokens']:,}",
                    f"Requests: {totals['requests']:,}",
                    f"Est cost: {cost_display}",
                    f"Last updated: {dt.datetime.utcnow():%H:%M:%S}Z",
                ]
            )
        )

        if alerts:
            self.alert_var.set("Alerts: " + "; ".join(alerts))
        else:
            self.alert_var.set("")

    def show_error(self, message: str) -> None:
        self.status_var.set(f"Error: {message}")
        self.alert_var.set("Check Admin key, API key ID, and network connectivity.")

    def run(self) -> None:
        self.root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GUI wrapper for tracking OpenAI API key usage without Terminal.",
    )
    parser.add_argument(
        "--admin-key",
        dest="admin_key",
        help="OpenAI Admin API key. Defaults to OPENAI_ADMIN_KEY environment variable.",
    )
    parser.add_argument(
        "--api-key-id",
        dest="api_key_id",
        help=(
            "The project API key ID to track (looks like key_...). "
            "Falls back to OPENAI_API_KEY_ID if not provided."
        ),
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
        choices=sorted(usage_tracker.COST_RATES.keys()),
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
    parser.add_argument(
        "--geometry",
        dest="geometry",
        default="1000x520",
        help="Tk window size (e.g., 1100x600).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gui = UsageTrackerGUI(args)
    gui.run()


if __name__ == "__main__":
    main()
