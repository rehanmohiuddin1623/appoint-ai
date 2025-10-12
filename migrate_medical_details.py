#!/usr/bin/env python3
"""
Migration script to add medical details columns to the users table.
Run this script to update your existing database with the new medical fields.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_medical_details():
    """Add medical details columns to the users table"""
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medassist")
    
    # For psycopg3, we need to use the proper driver
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # SQL statements to add new columns
        migration_queries = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS blood_sugar_avg_without_tablets VARCHAR;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS blood_pressure VARCHAR;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS blood_group VARCHAR;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tsh_thyroid_value VARCHAR;"
        ]
        
        print("Starting medical details migration...")
        
        # Execute migration queries
        with engine.connect() as connection:
            for query in migration_queries:
                print(f"Executing: {query}")
                connection.execute(text(query))
                connection.commit()
        
        print("✅ Migration completed successfully!")
        print("New medical details columns added to users table:")
        print("  - full_name")
        print("  - blood_sugar_avg_without_tablets")
        print("  - blood_pressure")
        print("  - blood_group")
        print("  - tsh_thyroid_value")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("Medical Details Migration Script")
    print("=" * 40)
    
    # Check if database URL is configured
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable not found!")
        print("Please set DATABASE_URL in your .env file or environment variables.")
        sys.exit(1)
    
    # Run migration
    success = migrate_medical_details()
    
    if success:
        print("\n🎉 You can now use the new POST /auth/me endpoint to update user medical details!")
        sys.exit(0)
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
        sys.exit(1)