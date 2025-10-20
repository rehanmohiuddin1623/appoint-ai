#!/usr/bin/env python3
"""
Database migration script to add weight field to users table
This script adds the weight column to existing user records.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.exc import OperationalError, ProgrammingError

def add_weight_column():
    """Add weight column to users table"""
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    # For psycopg3, we need to use the proper driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    print("🔄 Adding weight column to users table...")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if weight column already exists
            check_column_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='weight';
            """)
            
            result = conn.execute(check_column_query)
            existing_column = result.fetchone()
            
            if existing_column:
                print("✅ Weight column already exists in users table")
                return True
            
            # Add weight column
            add_column_query = text("""
                ALTER TABLE users 
                ADD COLUMN weight VARCHAR;
            """)
            
            conn.execute(add_column_query)
            conn.commit()
            
            print("✅ Weight column added successfully to users table")
            return True
            
    except OperationalError as e:
        print(f"❌ Database operation error: {e}")
        print("Make sure PostgreSQL is running and the database exists")
        return False
    except ProgrammingError as e:
        print(f"❌ SQL error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_weight_column():
    """Verify that the weight column was added successfully"""
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False
    
    # For psycopg3, we need to use the proper driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if weight column exists and get its details
            verify_query = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='weight';
            """)
            
            result = conn.execute(verify_query)
            column_info = result.fetchone()
            
            if column_info:
                print(f"✅ Weight column verified:")
                print(f"   - Column name: {column_info[0]}")
                print(f"   - Data type: {column_info[1]}")
                print(f"   - Nullable: {column_info[2]}")
                return True
            else:
                print("❌ Weight column not found")
                return False
                
    except Exception as e:
        print(f"❌ Error verifying weight column: {e}")
        return False

def main():
    """Main migration function"""
    print("🏥 Med Assist Agent - Weight Column Migration")
    print("=" * 50)
    
    # Add weight column
    if not add_weight_column():
        print("\n❌ Migration failed!")
        sys.exit(1)
    
    # Verify the migration
    if not verify_weight_column():
        print("\n❌ Migration verification failed!")
        sys.exit(1)
    
    print("\n✅ Weight column migration completed successfully!")
    print("\n📝 The weight field has been added to the users table.")
    print("Users can now update their weight information via:")
    print("- GET /auth/me - to view current weight")
    print("- POST /auth/me - to update weight along with other medical details")
    print("\n🔄 You may need to restart your API server to apply the changes.")

if __name__ == "__main__":
    main()