#!/usr/bin/env bash
set -euo pipefail

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

"$PYTHON" scripts/download_gdpr.py
"$PYTHON" -m ingestion.ingest_documents --skip-qdrant
