#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
npm --prefix web ci --no-fund
npm --prefix web run build
.venv/bin/pip check
