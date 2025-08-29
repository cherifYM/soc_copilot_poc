#!/usr/bin/env bash
# scripts/fix_imports.sh
# One-shot fixer for your "Import ... could not be resolved" problems.
# Creates venv, installs deps, and patches minimal files (db.py/hooks.py) safely.
set -euo pipefail

# --- 0) Python & venv --------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Install Python 3.10+ first." >&2; exit 1;
fi

python3 - <<'PY'
import sys
assert sys.version_info >= (3,10), f"Need Python 3.10+. Found: {sys.version.split()[0]}"
print(f"✅ Using Python {sys.version.split()[0]}")
PY

python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip setuptools wheel

# --- 1) Requirements ---------------------------------------------------------
cat > requirements.txt <<'REQ'
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
SQLAlchemy==2.0.35
python-dotenv==1.0.1
requests==2.32.3
httpx==0.27.2
pytest==8.3.2
streamlit==1.38.0
REQ

pip install -r requirements.txt

# --- 2) Project structure (non-destructive) ----------------------------------
mkdir -p app/api app/core app/pipeline app/playbooks
[ -f app/__init__.py ] || : > app/__init__.py
[ -f app/api/__init__.py ] || : > app/api/__init__.py
[ -f app/core/__init__.py ] || : > app/core/__init__.py
[ -f app/pipeline/__init__.py ] || : > app/pipeline/__init__.py
[ -f app/playbooks/__init__.py ] || : > app/playbooks/__init__.py

# --- 3) db.py (both root and app/core) --------------------------------------
# If you already have these files, they won't be overwritten unless you pass --force
FORCE=${1:-}
write_file() { # path, heredoc-name
  local path="$1"; local tag="$2";
  if [[ -f "$path" && "$FORCE" != "--force" ]]; then
    echo "↷ Skipping existing $path (use --force to overwrite)"; return 0; fi
  mkdir -p "$(dirname "$path")"; cat > "$path" <<"PY"
from __future__ import annotations
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./soc.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it.
    Keep this exact signature for `Depends(get_db)`.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
PY
}

write_file app/core/db.py PY
write_file db.py PY

# --- 4) hooks.py minimal (safe no-op) ---------------------------------------
if [[ ! -f hooks.py || "$FORCE" == "--force" ]]; then
  cat > hooks.py <<'PY'
from __future__ import annotations
# This file is optional; it just ensures your imports resolve.
from sqlalchemy import event
from sqlalchemy.orm import Session
from db import engine  # or from app.core.db import engine if you prefer package import

# Example: simple connect listener (no-op for sqlite)
@event.listens_for(engine, "connect")
def on_connect(dbapi_conn, connection_record):
    # Intentionally no-op; add pragmas here for sqlite if needed.
    pass
PY
else
  echo "↷ Skipping hooks.py (exists)"
fi

# --- 5) Quick import smoke test ---------------------------------------------
python - <<'PY'
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlalchemy
from sqlalchemy.orm import Session
import dotenv
from fastapi.testclient import TestClient
import streamlit, requests
print("✅ Imports: fastapi, pydantic, sqlalchemy, dotenv, testclient, streamlit OK")
PY

cat <<'EOS'

Next steps:
  1) Select the interpreter in your editor: ./.venv (VS Code: Cmd/Ctrl+Shift+P → Python: Select Interpreter).
  2) Run API (adjust module path if needed):
       uvicorn app.api.main:app --reload --port 8000
  3) Run tests:
       pytest -q
  4) Run streamlit app:
       streamlit run streamlit.py

Tip: if an import still looks unresolved in the editor, it’s almost always the wrong interpreter selected.
EOS
