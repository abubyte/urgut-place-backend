#!/usr/bin/env python3
"""Test database connection"""
import sys
from app.db.session import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print("✓ Database connection successful!")
        print(f"  PostgreSQL version: {version[:50]}...")
        sys.exit(0)
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    sys.exit(1)
