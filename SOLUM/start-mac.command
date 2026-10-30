#!/bin/sh
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  open http://localhost:8000
  python3 server.py
else
  echo 'Install Python 3.10 or newer from python.org, then try again.'
  read -r answer
fi
