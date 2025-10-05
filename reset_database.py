#!/usr/bin/env python3
"""
Database Reset Script
====================

This script will:
1. Drop all existing tables
2. Recreate the database schema with authentication
3. Initialize fresh tables

WARNING: This will delete ALL existing data!
"""

import os
from sqlalchemy import create_engine, text
from database import DATABASE_URL, Base, engine
from dotenv import load_dotenv

load_dotenv()

def reset_database():
    """Reset the entire database"""
    print("🗑️  Resetting database...")
    print("⚠️  WARNING: This will delete ALL existing data!")
    
    # Confirm action
    response = input("Are you sure you want to delete all data? Type 'DELETE' to confirm: ")
    if response != 'DELETE':
        print("❌ Database reset cancelled.")
        return False
    
    try:
        # Create engine
        db_engine = create_engine(DATABASE_URL)
        
        with db_engine.connect() as connection:
            print("🔄 Starting database reset...")
            
            # Drop all tables and types
            print("🗑️  Dropping all tables and types...")
            connection.execute(text("""
                -- Drop tables with CASCADE to handle foreign keys
                DROP TABLE IF EXISTS appointment_calls CASCADE;
                DROP TABLE IF EXISTS appointment_calls_backup CASCADE;
                DROP TABLE IF EXISTS users CASCADE;
                
                -- Drop custom types
                DROP TYPE IF EXISTS appointmentstate CASCADE;
            """))
            
            connection.commit()
            print("✅ All tables and types dropped successfully!")
            
        # Now recreate all tables using SQLAlchemy
        print("📝 Creating fresh database schema...")
        Base.metadata.create_all(bind=db_engine)
        print("✅ Database schema created successfully!")
        
        # Verify tables were created
        with db_engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📊 Created tables: {tables}")
            
            # Check column structure for appointment_calls
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'appointment_calls'
                ORDER BY ordinal_position;
            """))
            
            print("\n🔍 appointment_calls table structure:")
            for col in result.fetchall():
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"   {col[0]}: {col[1]} ({nullable})")
        
        print("\n🎉 Database reset completed successfully!")
        print("📝 Your database is now ready with the authentication system.")
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🏥 Med-Assist Database Reset")
    print("=" * 40)
    reset_database()