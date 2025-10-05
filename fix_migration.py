"""
Fixed Database Migration Script for User Authentication and Appointment Management
================================================================================

This script fixes the migration issues by properly handling existing data and enum conversions.
"""

import os
from sqlalchemy import create_engine, text
from database import DATABASE_URL
from dotenv import load_dotenv

load_dotenv()

def run_fixed_migration():
    """Run the fixed database migration"""
    engine = create_engine(DATABASE_URL)
    
    print("🔄 Starting fixed database migration...")
    
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
                
                # 3. Check current table structure
                print("🔍 Checking current table structure...")
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'appointment_calls'
                    ORDER BY ordinal_position;
                """))
                
                columns = result.fetchall()
                existing_columns = {col[0]: col[1] for col in columns}
                print(f"Existing columns: {list(existing_columns.keys())}")
                
                # 4. Back up the table
                print("📋 Backing up existing appointment_calls table...")
                connection.execute(text("""
                    DROP TABLE IF EXISTS appointment_calls_backup;
                    CREATE TABLE appointment_calls_backup AS 
                    SELECT * FROM appointment_calls;
                """))
                
                # 5. Add user_id column if it doesn't exist
                if 'user_id' not in existing_columns:
                    print("➕ Adding user_id column...")
                    connection.execute(text("""
                        ALTER TABLE appointment_calls 
                        ADD COLUMN user_id INTEGER;
                    """))
                else:
                    print("✅ user_id column already exists")
                
                # 6. Handle appointment_state column conversion
                if 'appointment_state' in existing_columns:
                    current_type = existing_columns['appointment_state']
                    print(f"📝 Current appointment_state type: {current_type}")
                    
                    if current_type != 'USER-DEFINED':  # Not an enum yet
                        print("🔄 Converting appointment_state to enum...")
                        
                        # First, update any invalid values to valid enum values
                        connection.execute(text("""
                            UPDATE appointment_calls 
                            SET appointment_state = CASE 
                                WHEN LOWER(appointment_state::text) = 'created' THEN 'created'
                                WHEN LOWER(appointment_state::text) = 'confirmed' THEN 'confirmed'
                                WHEN LOWER(appointment_state::text) = 'rejected' THEN 'rejected'
                                WHEN LOWER(appointment_state::text) = 'expired' THEN 'expired'
                                ELSE 'created'
                            END;
                        """))
                        
                        # Convert the column to enum type
                        connection.execute(text("""
                            ALTER TABLE appointment_calls 
                            ALTER COLUMN appointment_state TYPE appointmentstate 
                            USING appointment_state::appointmentstate;
                        """))
                    else:
                        print("✅ appointment_state is already an enum")
                else:
                    print("➕ Adding appointment_state column...")
                    connection.execute(text("""
                        ALTER TABLE appointment_calls 
                        ADD COLUMN appointment_state appointmentstate DEFAULT 'created'::appointmentstate;
                    """))
                
                # 7. Add retry columns if they don't exist
                if 'retry_count' not in existing_columns:
                    print("➕ Adding retry columns...")
                    connection.execute(text("""
                        ALTER TABLE appointment_calls 
                        ADD COLUMN retry_count INTEGER DEFAULT 0,
                        ADD COLUMN max_retries INTEGER DEFAULT 3;
                    """))
                else:
                    print("✅ Retry columns already exist")
                
                # 8. Create a default user for existing appointments
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
                
                # 9. Update existing appointments to use default user
                print("🔗 Linking existing appointments to default user...")
                connection.execute(text("""
                    UPDATE appointment_calls 
                    SET user_id = :user_id 
                    WHERE user_id IS NULL;
                """), {"user_id": default_user_id})
                
                # 10. Add foreign key constraint
                print("🔗 Adding foreign key constraint...")
                try:
                    connection.execute(text("""
                        ALTER TABLE appointment_calls 
                        ADD CONSTRAINT fk_appointment_user 
                        FOREIGN KEY (user_id) REFERENCES users(id);
                    """))
                except Exception as e:
                    if "already exists" in str(e):
                        print("✅ Foreign key constraint already exists")
                    else:
                        print(f"Note: Foreign key constraint issue: {e}")
                
                # 11. Make user_id NOT NULL
                print("🔒 Making user_id NOT NULL...")
                connection.execute(text("""
                    ALTER TABLE appointment_calls 
                    ALTER COLUMN user_id SET NOT NULL;
                """))
                
                # 12. Create indexes for better performance
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
                print(f"   📋 Backup table: appointment_calls_backup")
                
                # Verify the final structure
                print("\n🔍 Final table structure:")
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'appointment_calls'
                    ORDER BY ordinal_position;
                """))
                
                for col in result.fetchall():
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    print(f"   {col[0]}: {col[1]} ({nullable})")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                print("🔄 Transaction rolled back.")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Med-Assist Fixed Database Migration")
    print("=" * 50)
    
    # Run migration
    if run_fixed_migration():
        print("\n🎉 Migration completed successfully!")
        print("📝 Your database is now ready for the new authentication system.")
    else:
        print("\n❌ Migration failed!")
        print("   Please check the error messages above and try again.")