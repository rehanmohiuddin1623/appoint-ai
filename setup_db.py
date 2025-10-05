#!/usr/bin/env python3
"""
Database setup script for Med Assist Agent
This script creates the database tables and verifies the connection.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from database import create_tables, init_database

def test_database_connection():
    """Test if we can connect to the database"""
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    print(f"🔗 Testing connection to: {database_url}")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n📋 Troubleshooting steps:")
        print("1. Make sure PostgreSQL is running on localhost:5432")
        print("2. Update DATABASE_URL in .env with correct username/password")
        print("3. Create the database if it doesn't exist:")
        print("   psql -U username -c 'CREATE DATABASE medassist;'")
        return False

def setup_database():
    """Set up database tables"""
    load_dotenv()
    
    print("🚀 Setting up database tables...")
    
    if not test_database_connection():
        return False
    
    try:
        if init_database():
            print("✅ Database tables created successfully!")
            return True
        else:
            print("❌ Failed to create database tables")
            return False
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def main():
    """Main setup function"""
    print("🏥 Med Assist Agent - Database Setup")
    print("=" * 40)
    
    # Test connection first
    if not test_database_connection():
        sys.exit(1)
    
    # Set up tables
    if not setup_database():
        sys.exit(1)
    
    print("\n✅ Database setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Update your DATABASE_URL in .env with your actual PostgreSQL credentials")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Start the API: python main.py")

if __name__ == "__main__":
    main()