#!/usr/bin/env bash
set -euo pipefail

# Create workplace/destination if missing
mkdir -p /tmp/workplace /tmp/destination

# Wait for the server to be ready
sleep 5

# Send config and start service in one request using a heredoc.
# Note: use a single-quoted heredoc marker ('JSON') so shell doesn't expand anything.
curl -s -X POST http://localhost:8080/api/v1/start \
  -H "Content-Type: application/json" -d @- <<'JSON'
{
  "workplace_path": "/tmp/workplace",
  "destination_root": "/tmp/destination",
  "stable_wait_seconds": 5.0,
  "dry_run_mode": true,
  "status_keywords": ["signed","executed","final"],
  "filename_pattern": "^(?P<doc>.+?)_(?P<client>.+?)_(?P<date>\\d{4}-?\\d{2}-?\\d{2})_(?P<status>.+?)\\.pdf$",
  "log_level": "INFO"
}
JSON