#!/usr/bin/env bash
# Simple script to install Flask packages into a pyenv-managed Python.
# Usage: ./setup-python.sh [python-version]
set -e

PYENV_CMD=$(command -v pyenv || true)
if [ -z "$PYENV_CMD" ]; then
  echo "pyenv not found. Install pyenv first: https://github.com/pyenv/pyenv"
  exit 1
fi

REQ_VERSION=${1:-3.13.0}

if ! pyenv versions --bare | grep -q "^${REQ_VERSION}$"; then
  echo "Python ${REQ_VERSION} is not installed under pyenv."
  echo "Install it with: pyenv install ${REQ_VERSION}"
  exit 1
fi

echo "Activating pyenv Python ${REQ_VERSION} for this shell..."
pyenv shell "${REQ_VERSION}"

echo "Upgrading pip and installing packages via python -m pip..."
python -m ensurepip --upgrade 2>/dev/null || true
python -m pip install --upgrade pip
python -m pip install flask flask-socketio flask-cors watchdog requests eventlet

echo "Done. Packages installed into pyenv Python ${REQ_VERSION}."