#!/usr/bin/env python3
"""
Simple database migration script
Creates initial schema for the sample application
"""
import os
import sys
import psycopg2
from psycopg2 import sql

# Database connection parameters from environment
DB_HOST = os.getenv('DATABASE_HOST', 'localhost')
DB_PORT = os.getenv('DATABASE_PORT', '5432')
DB_NAME = os.getenv('DATABASE_NAME', 'sampleapp')
DB_USER = os.getenv('DATABASE_USER', 'appuser')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD', 'demo_password_123')

def create_api_keys_table(conn):
    """Create API keys table for persistent storage"""
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                api_key VARCHAR(255) UNIQUE NOT NULL,
                user_name VARCHAR(100) NOT NULL,
                roles TEXT[] NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Create indexes separately (PostgreSQL syntax)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys(api_key);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_user_name ON api_keys(user_name);
        """)
        
        conn.commit()
        print("API keys table created successfully")
    except Exception as e:
        conn.rollback()
        print(f"Failed to create api_keys table: {e}")
        raise
    finally:
        cur.close()

# Note: create_users_table is now integrated into create_schema()
# This function is kept for reference but users table is created in create_schema()

def create_schema():
    """Create database schema"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print(f"Connected to database: {DB_NAME}")
        
        # Create users table (with auth fields)
        print("Creating users table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE,
                password_hash VARCHAR(255),
                roles TEXT[] NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        
        # Add indexes for users table
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        """)
        
        # Create requests_log table
        print("Creating requests_log table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS requests_log (
                id SERIAL PRIMARY KEY,
                endpoint VARCHAR(255) NOT NULL,
                method VARCHAR(10) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create index on requests_log
        print("Creating indexes...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_requests_log_created_at 
            ON requests_log(created_at);
        """)
        
        # Create updated_at trigger function
        print("Creating trigger function...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Create trigger on users table
        cur.execute("""
            DROP TRIGGER IF EXISTS update_users_updated_at ON users;
            CREATE TRIGGER update_users_updated_at
                BEFORE UPDATE ON users
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        # Create API keys table
        print("Creating api_keys table...")
        create_api_keys_table(conn)
        
        cur.close()
        conn.close()
        
        print("? Schema created successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"? Database error: {e}")
        return False
    except Exception as e:
        print(f"? Error: {e}")
        return False

def drop_schema():
    """Drop database schema (for testing)"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Dropping schema...")
        cur.execute("DROP TABLE IF EXISTS requests_log CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        cur.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")
        
        cur.close()
        conn.close()
        
        print("? Schema dropped successfully!")
        return True
        
    except Exception as e:
        print(f"? Error: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'drop':
        if input("Are you sure you want to drop all tables? (yes/no): ") == 'yes':
            drop_schema()
        else:
            print("Cancelled.")
    else:
        print("Running database migration...")
        print(f"Database: {DB_NAME}@{DB_HOST}:{DB_PORT}")
        print("-" * 50)
        create_schema()
