#!/usr/bin/env python3
"""Simple, policy-compliant YouTube Live monitor.

This script replaces fake/bot view behavior with legitimate analytics polling
through the YouTube Data API v3.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

import requests

API_URL = "https://www.googleapis.com/youtube/v3/videos"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Monitor a YouTube live video's public metrics using YouTube Data API."
        )
    )
    parser.add_argument("video_id", help="YouTube video ID to monitor")
    parser.add_argument(
        "--api-key",
        default=os.getenv("YOUTUBE_API_KEY", ""),
        help="YouTube Data API key (or set YOUTUBE_API_KEY)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Polling interval in seconds (default: 30)",
    )
    return parser.parse_args()


def fetch_live_details(video_id: str, api_key: str, timeout: int = 15) -> dict[str, Any]:
    params = {
        "part": "snippet,liveStreamingDetails,statistics",
        "id": video_id,
        "key": api_key,
    }
    response = requests.get(API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    items = payload.get("items", [])
    if not items:
        raise ValueError("No video found for the provided video_id")

    return items[0]


def fmt_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def print_snapshot(video: dict[str, Any]) -> None:
    snippet = video.get("snippet", {})
    live = video.get("liveStreamingDetails", {})
    stats = video.get("statistics", {})

    title = snippet.get("title", "(unknown title)")
    channel = snippet.get("channelTitle", "(unknown channel)")
    live_viewers = live.get("concurrentViewers", "N/A")
    total_views = stats.get("viewCount", "N/A")
    started_at = live.get("actualStartTime", "N/A")

    print(f"[{fmt_now()}] {title} — {channel}")
    print(
        f"  concurrent_viewers={live_viewers} | total_views={total_views} | started_at={started_at}"
    )


def main() -> int:
    args = parse_args()

    if not args.api_key:
        print(
            "Error: Missing API key. Pass --api-key or set YOUTUBE_API_KEY.",
            file=sys.stderr,
        )
        return 2

    if args.interval < 5:
        print("Error: --interval must be >= 5 seconds.", file=sys.stderr)
        return 2

    print("YouTube Live Monitor started. Press Ctrl+C to stop.")
    print(f"Video ID: {args.video_id}")
    print(f"Poll interval: {args.interval}s")

    while True:
        try:
            video = fetch_live_details(args.video_id, args.api_key)
            print_snapshot(video)
        except requests.HTTPError as exc:
            print(f"[{fmt_now()}] HTTP error: {exc}", file=sys.stderr)
        except requests.RequestException as exc:
            print(f"[{fmt_now()}] Network error: {exc}", file=sys.stderr)
        except ValueError as exc:
            print(f"[{fmt_now()}] Data error: {exc}", file=sys.stderr)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
