#!/usr/bin/env bash
# Convenience runner. Default backend is mock (no key needed).
set -e
python -m quantummind.run --all
python -m quantummind.run --eval
