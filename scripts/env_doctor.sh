#!/usr/bin/env bash
# scripts/env_doctor.sh
# Diagnose why uvicorn/pytest/streamlit aren't found and optionally fix.
set -euo pipefail

FIX=${1:-}

say() { printf "\n▶ %s\n" "$*"; }
err() { printf "\n❌ %s\n" "$*" 1>&2; }
ok()  { printf "✅ %s\n" "$*"; }

say "Shell: $SHELL"
command -v python3 >/dev/null || { err "python3 not found"; exit 1; }
PY=$(command -v python3)
say "python3: $PY"
python3 -c 'import sys; print("Python:", sys.version.split()[0])'

# 1) Ensure venv exists & active
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  err "Virtualenv not active. Run:  source .venv/bin/activate"
  if [[ ! -d .venv ]]; then
    say "Creating .venv..."; python3 -m venv .venv
  fi
  exit 1
else
  ok "Virtualenv active: $VIRTUAL_ENV"
fi

say "python in venv: $(command -v python)"
python -m pip -V || true

# 2) Check packages installed
need_install=()
for pkg in uvicorn pytest streamlit fastapi pydantic SQLAlchemy python-dotenv; do
  if ! python - <<PY >/dev/null 2>&1
import importlib, sys
name = {
  'SQLAlchemy': 'sqlalchemy',
  'python-dotenv': 'dotenv',
}.get('$pkg', '$pkg')
importlib.import_module(name)
PY
  then
    need_install+=("$pkg")
  fi
done

if ((${#need_install[@]})); then
  err "Missing: ${need_install[*]}"
  if [[ "$FIX" == "--fix" ]]; then
    say "Installing missing packages..."
    python -m pip install -U pip setuptools wheel
    python -m pip install "uvicorn[standard]" pytest streamlit fastapi pydantic SQLAlchemy python-dotenv
    ok "Installed."
  else
    say "Run with --fix to install them automatically:  bash scripts/env_doctor.sh --fix"
    exit 2
  fi
else
  ok "All required packages importable"
fi

# 3) Check CLI scripts exist
for bin in uvicorn pytest streamlit; do
  if [[ -x "$VIRTUAL_ENV/bin/$bin" ]]; then
    ok "$bin found: $VIRTUAL_ENV/bin/$bin"
  else
    err "$bin missing from venv bin"
  fi
done

# 4) Offer module path to run
APP_PATH=""
if [[ -f app/api/main.py ]]; then
  APP_PATH="app.api.main:app"
elif [[ -f main.py ]]; then
  APP_PATH="main:app"
else
  err "Could not find app/api/main.py or main.py"
fi

if [[ -n "$APP_PATH" ]]; then
  say "Run API via python -m to avoid PATH issues:"
  echo "  python -m uvicorn $APP_PATH --reload --port 8000"
fi

say "Run tests / streamlit via python -m as well:"
echo "  python -m pytest -q"
echo "  python -m streamlit run streamlit.py"

say "(zsh only) refresh hash table after installs:  rehash"

ok "Doctor finished."
