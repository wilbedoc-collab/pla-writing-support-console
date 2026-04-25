#!/bin/zsh
set -euo pipefail
cd /Users/ahnbot/.openclaw/workspace
exec /usr/bin/python3 /Users/ahnbot/.openclaw/workspace/review_ui_v2/server.py >> /Users/ahnbot/.openclaw/workspace/review_ui_v2/server.log 2>&1
