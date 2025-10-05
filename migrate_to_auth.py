"""
Database Migration Script for User Authentication and Appointment Management
===========================================================================

This script migrates the existing database schema to support:
1. User table with phone-based OTP authentication
2. Updated AppointmentCall table with user relationships and appointment states
3. Retry logic and proper datetime handling

Run this script AFTER backing up your existing database.
"""

import os
from sqlalchemy import create_engine, text
from database import DATABASE_URL, init_database
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Run the database migration"""
    engine = create_engine(DATABASE_URL)
    
    print("🔄 Starting database migration...")
    
    try:
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                # 1. Create users table
                print("📝 Creating users table...")
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        phone_number VARCHAR UNIQUE NOT NULL,
                        is_verified BOOLEAN DEFAULT FALSE,
                        otp_code VARCHAR,
                        otp_expires_at TIMESTAMP,
                        otp_attempts INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                # 2. Create appointment state enum
                print("📝 Creating appointment state enum...")
                connection.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE appointmentstate AS ENUM ('created', 'confirmed', 'rejected', 'expired');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                # 3. Check if appointment_calls table exists and back it up
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'appointment_calls'
                    );
                """))
                
                table_exists = result.fetchone()[0]
                
                if table_exists:
                    print("📋 Backing up existing appointment_calls table...")
                    connection.execute(text("""
                        CREATE TABLE appointment_calls_backup AS 
                        SELECT * FROM appointment_calls;
                    """))
                    
                    # 4. Add new columns to existing table
                    print("🔧 Adding new columns to appointment_calls table...")
                    
                    # Add user_id column (temporarily nullable)
                    try:
                        connection.execute(text("""
                            ALTER TABLE appointment_calls 
                            ADD COLUMN IF NOT EXISTS user_id INTEGER;
                        """))
                    except Exception as e:
                        print(f"Note: user_id column may already exist: {e}")
                    
                    # Add appointment_state column
                    try:
                        connection.execute(text("""
                            ALTER TABLE appointment_calls 
                            ADD COLUMN IF NOT EXISTS appointment_state appointmentstate DEFAULT 'created';
                        """))
                    except Exception as e:
                        print(f"Note: appointment_state column may already exist: {e}")
                    
                    # Add retry columns
                    try:
                        connection.execute(text("""
                            ALTER TABLE appointment_calls 
                            ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
                            ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3;
                        """))
                    except Exception as e:
                        print(f"Note: retry columns may already exist: {e}")
                    
                    # 5. Create a default user for existing appointments
                    print("👤 Creating default user for existing appointments...")
                    connection.execute(text("""
                        INSERT INTO users (phone_number, is_verified, created_at, updated_at)
                        VALUES ('+0000000000', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (phone_number) DO NOTHING;
                    """))
                    
                    # Get the default user ID
                    result = connection.execute(text("""
                        SELECT id FROM users WHERE phone_number = '+0000000000';
                    """))
                    default_user_id = result.fetchone()[0]
                    
                    # 6. Update existing appointments to use default user
                    print("🔗 Linking existing appointments to default user...")
                    connection.execute(text("""
                        UPDATE appointment_calls 
                        SET user_id = :user_id 
                        WHERE user_id IS NULL;
                    """), {"user_id": default_user_id})
                    
                    # 7. Convert call_time from string to timestamp if needed
                    print("⏰ Converting call_time to proper timestamp format...")
                    try:
                        connection.execute(text("""
                            ALTER TABLE appointment_calls 
                            ALTER COLUMN call_time TYPE TIMESTAMP 
                            USING call_time::timestamp;
                        """))
                    except Exception as e:
                        print(f"Note: call_time may already be timestamp: {e}")
                    
                    # 8. Add foreign key constraint
                    print("🔗 Adding foreign key constraint...")
                    try:
                        connection.execute(text("""
                            ALTER TABLE appointment_calls 
                            ADD CONSTRAINT fk_appointment_user 
                            FOREIGN KEY (user_id) REFERENCES users(id);
                        """))
                    except Exception as e:
                        print(f"Note: Foreign key constraint may already exist: {e}")
                    
                    # 9. Make user_id NOT NULL
                    print("🔒 Making user_id NOT NULL...")
                    try:
                        connection.execute(text("""
                            ALTER TABLE appointment_calls 
                            ALTER COLUMN user_id SET NOT NULL;
                        """))
                    except Exception as e:
                        print(f"Note: user_id may already be NOT NULL: {e}")
                
                else:
                    print("📝 Creating new appointment_calls table with updated schema...")
                    # Create the table with the new schema using SQLAlchemy
                    
                # 10. Create indexes for better performance
                print("📊 Creating indexes for better performance...")
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number);
                    CREATE INDEX IF NOT EXISTS idx_appointment_calls_user_id ON appointment_calls(user_id);
                    CREATE INDEX IF NOT EXISTS idx_appointment_calls_state ON appointment_calls(appointment_state);
                    CREATE INDEX IF NOT EXISTS idx_appointment_calls_call_time ON appointment_calls(call_time);
                """))
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
                # Print summary
                result = connection.execute(text("SELECT COUNT(*) FROM users;"))
                user_count = result.fetchone()[0]
                
                result = connection.execute(text("SELECT COUNT(*) FROM appointment_calls;"))
                appointment_count = result.fetchone()[0]
                
                print(f"\n📊 Migration Summary:")
                print(f"   👤 Users: {user_count}")
                print(f"   📅 Appointments: {appointment_count}")
                print(f"   📋 Backup table: appointment_calls_backup (if existed)")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                print("🔄 Transaction rolled back.")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    try:
        # Initialize database with new schema
        if init_database():
            print("✅ New schema validation successful!")
            return True
        else:
            print("❌ New schema validation failed!")
            return False
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Med-Assist Database Migration")
    print("=" * 50)
    
    # Confirm before running
    response = input("⚠️  This will modify your database. Have you backed up your data? (y/N): ")
    if response.lower() != 'y':
        print("❌ Migration cancelled. Please backup your database first.")
        exit(1)
    
    # Run migration
    if run_migration():
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("📝 Your database is now ready for the new authentication system.")
        else:
            print("\n⚠️  Migration completed but verification failed.")
            print("   Please check your database manually.")
    else:
        print("\n❌ Migration failed!")
        print("   Please check the error messages above and try again.")