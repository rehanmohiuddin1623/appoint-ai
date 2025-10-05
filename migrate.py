#!/usr/bin/env python3
"""
Database migration utilities for Med Assist Agent
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from database import Base, engine

load_dotenv()

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found in environment")
        return False
    
    # Extract database name from URL
    db_name = database_url.split('/')[-1]
    
    # Create connection to postgres database to create our target database
    base_url = database_url.rsplit('/', 1)[0]
    postgres_url = f"{base_url}/postgres"
    
    try:
        temp_engine = create_engine(postgres_url)
        with temp_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
            if result.fetchone():
                print(f"Database '{db_name}' already exists")
                return True
            
            # Create database
            conn.execute(text("COMMIT"))  # End any open transaction
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"Database '{db_name}' created successfully")
            return True
            
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def drop_all_tables():
    """Drop all tables (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        print("All tables dropped successfully")
        return True
    except Exception as e:
        print(f"Error dropping tables: {e}")
        return False

def create_all_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

def reset_database():
    """Reset the entire database (drop and recreate tables)"""
    print("⚠️  Resetting database (this will delete all data)")
    
    if drop_all_tables() and create_all_tables():
        print("✅ Database reset completed")
        return True
    else:
        print("❌ Database reset failed")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [create|reset|drop]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "create":
        create_database_if_not_exists()
        create_all_tables()
    elif action == "reset":
        reset_database()
    elif action == "drop":
        drop_all_tables()
    else:
        print("Unknown action. Use: create, reset, or drop")
        sys.exit(1)