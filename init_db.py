#!/usr/bin/env python3
"""
init_db.py

Initialize the PostgreSQL database schema for JarvisAssistant
by creating tables defined in db.py models.
"""

import os
import sys
from sqlalchemy import create_engine

# Import Base and default DATABASE_URL from your db.py
from db import Base, DATABASE_URL as DEFAULT_DATABASE_URL


def init_db(database_url: str):
    """
    Create all tables in the specified database.
    """
    engine = create_engine(database_url, echo=True)
    Base.metadata.create_all(engine)
    print(f"✅  Initialized database schema on {database_url}")


def main():
    # Determine the database URL: env var overrides default
    db_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    # Allow passing the URL as a command-line argument
    if len(sys.argv) > 1:
        db_url = sys.argv[1]

    init_db(db_url)


if __name__ == "__main__":
    main()
