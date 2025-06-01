"""
Database utilities for We-Relate Flask app
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash


def get_db_path():
    """Get the database path from environment or default"""
    return os.environ.get('DATABASE_PATH', 'app.db')


def init_db():
    """Initialize the database with required tables"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            tier TEXT DEFAULT 'free',
            credits INTEGER DEFAULT 100,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add admin column to existing users table if it doesn't exist
    cursor.execute('''
        PRAGMA table_info(users)
    ''')
    columns = [column[1] for column in cursor.fetchall()]
    if 'is_admin' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
    
    # Sessions table (keeping for potential future use)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tier TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP,
            stripe_subscription_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'usd',
            status TEXT DEFAULT 'pending',
            stripe_payment_intent_id TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()


def create_demo_user():
    """Create a demo user for testing"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', ('demo',))
        if not cursor.fetchone():
            demo_password = generate_password_hash('demo123')
            cursor.execute(
                'INSERT INTO users (username, email, first_name, last_name, password_hash, tier, credits) VALUES (?, ?, ?, ?, ?, ?, ?)',
                ('demo', 'demo@example.com', 'Demo', 'User', demo_password, 'premium', 500)
            )
            conn.commit()
            print("Demo user created: username=demo, password=demo123")
        conn.close()
    except Exception as e:
        print(f"Error creating demo user: {e}")


def create_admin_user():
    """Create an admin user for troubleshooting"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@we-relate.com',))
        if not cursor.fetchone():
            admin_password = generate_password_hash('admin123')
            cursor.execute(
                'INSERT INTO users (username, email, first_name, last_name, password_hash, tier, credits, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                ('admin@we-relate.com', 'admin@we-relate.com', 'Admin', 'User', admin_password, 'admin', 0, 1)
            )
            conn.commit()
            print("Admin user created: email=admin@we-relate.com, password=admin123")
        conn.close()
    except Exception as e:
        print(f"Error creating admin user: {e}") 