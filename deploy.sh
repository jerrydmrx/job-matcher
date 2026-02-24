#!/usr/bin/env bash
set -euo pipefail

# deploy.sh
# Usage: run this script on the server from the project directory to:
#  - install Python requirements into the detected virtualenv
#  - ensure templates are present in the deployment directory
#  - restart Passenger to pick up changes

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"

# Detect virtualenv: prefer env var VENV_DIR, then .venv, then common passenger venv path
VENV_DIR=""
if [ -z "$VENV_DIR" ]; then
  if [ -d "$PROJECT_DIR/.venv" ]; then
    VENV_DIR="$PROJECT_DIR/.venv"
  elif [ -d "/home/$(whoami)/virtualenv/job-matcher.osogbue.tech/3.13" ]; then
    VENV_DIR="/home/$(whoami)/virtualenv/job-matcher.osogbue.tech/3.13"
  fi
fi

echo "Project: $PROJECT_DIR"
if [ -n "$VENV_DIR" ] && [ -x "$VENV_DIR/bin/python" ]; then
  echo "Using virtualenv: $VENV_DIR"
  PIP="$VENV_DIR/bin/python -m pip"
else
  echo "No usable virtualenv detected. Set VENV_DIR to your project's venv and re-run." >&2
  exit 1
fi

if [ ! -f "$REQUIREMENTS" ]; then
  echo "requirements.txt not found at $REQUIREMENTS" >&2
  exit 1
fi

echo "Installing requirements..."
"$PIP" install -r "$REQUIREMENTS"

# Ensure templates directory exists in the deploy location
if [ -d "$PROJECT_DIR/templates" ]; then
  echo "Templates directory present: $PROJECT_DIR/templates"
else
  echo "Creating templates directory: $PROJECT_DIR/templates"
  mkdir -p "$PROJECT_DIR/templates"
fi

# Copy templates from the project to the deploy location if they exist
if [ -d "$PROJECT_DIR/templates" ] && [ -f "$PROJECT_DIR/templates/index.html" ]; then
  cp "$PROJECT_DIR/templates/index.html" "$PROJECT_DIR/templates/"
  echo "Copied templates to deploy location"
fi

# If a repo-level source (e.g. repo/templates) exists, copy it (safe overwrite)
if [ -d "$PROJECT_DIR/templates" ]; then
  echo "Ensuring templates are readable by web user"
  chmod -R a+r "$PROJECT_DIR/templates"
fi

# Restart Passenger: prefer passenger-config if available, otherwise touch tmp/restart.txt
echo "Restarting Passenger..."
if command -v passenger-config >/dev/null 2>&1; then
  passenger-config restart-app "$PROJECT_DIR" || true
else
  mkdir -p "$PROJECT_DIR/tmp"
  touch "$PROJECT_DIR/tmp/restart.txt"
fi

echo "Deploy complete. Check app.log and passenger_error.log for any errors."
