#!/usr/bin/env bash
set -euo pipefail

python3 -m py_compile \
  baseball_processor/main.py \
  baseball_processor/reports/source_parity.py \
  baseball_processor/website/generator.py \
  baseball_processor/website/parity.py \
  baseball_processor/website/react_app.py \
  baseball_processor/website/react_chunks/*.py \
  baseball_processor/website/serializers.py

if python3 -m ruff --version >/dev/null 2>&1; then
  python3 -m ruff check baseball_processor tests
else
  echo "ruff is not installed; skipping lint"
fi

python3 -m unittest discover -s tests

python3 -m baseball_processor --quick-stats --from-cache-only --skip-debut-update --no-emoji >/dev/null
