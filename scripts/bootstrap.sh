#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/homebrew/bin/python3.11}"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python 3.11 not found at ${PYTHON_BIN}" >&2
  echo "Install it with: brew install python@3.11" >&2
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${ROOT_DIR}/requirements.txt" httpx

echo
echo "Bootstrap complete."
echo "Activate: source .venv/bin/activate"
echo "Run web app: ./.venv/bin/python web_app/dash_app/app.py"
echo "Run tests: ./.venv/bin/python -m pytest tests/ -v --tb=short"
