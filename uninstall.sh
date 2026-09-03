#!/bin/bash
# Convenient wrapper for Antigravity Traffic Light uninstaller

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$REPO_DIR/scripts/uninstall.sh" "$@"
