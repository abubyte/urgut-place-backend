#!/bin/bash
# Activate virtual environment and run seed script
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || . venv/bin/activate
python -m app.db.seed_data
