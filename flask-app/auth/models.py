import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, Dict, Any

class User:
    """User model for authentication and user management"""
    
    def __init__(self, id=None, username=None, email=None, password_hash=None, 
                 tier='free', credits=100, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.tier = tier
        self.credits = credits
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def create(cls, username: str, email: str, password: str, tier: str = 'free') -> 'User':
        """Create a new user"""
        password_hash = generate_password_hash(password)
        
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, tier, credits) VALUES (?, ?, ?, ?, ?)',
                (username, email, password_hash, tier, 100 if tier == 'free' else 500)
            )
            user_id = cursor.lastrowid
            conn.commit()
            
            return cls.get_by_id(user_id)
        except sqlite3.IntegrityError:
            raise ValueError("Username or email already exists")
        finally:
            conn.close()
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """Get user by ID"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, email, password_hash, tier, credits, created_at FROM users WHERE id = ?',
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(*row)
        return None
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """Get user by username"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, email, password_hash, tier, credits, created_at FROM users WHERE username = ?',
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(*row)
        return None
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        """Get user by email"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, email, password_hash, tier, credits, created_at FROM users WHERE email = ?',
            (email,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(*row)
        return None
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches user's password"""
        return check_password_hash(self.password_hash, password)
    
    def update_credits(self, credits_used: int) -> bool:
        """Update user credits, return True if successful"""
        if self.credits < credits_used:
            return False
        
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET credits = credits - ? WHERE id = ? AND credits >= ?',
            (credits_used, self.id, credits_used)
        )
        
        success = cursor.rowcount > 0
        if success:
            self.credits -= credits_used
        
        conn.commit()
        conn.close()
        return success
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'tier': self.tier,
            'credits': self.credits,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

class UserSession:
    """User session model"""
    
    def __init__(self, id=None, user_id=None, session_token=None, 
                 created_at=None, expires_at=None):
        self.id = id
        self.user_id = user_id
        self.session_token = session_token
        self.created_at = created_at or datetime.now()
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=24))
    
    @classmethod
    def create(cls, user_id: int, session_token: str) -> 'UserSession':
        """Create a new session"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=24)
        cursor.execute(
            'INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)',
            (user_id, session_token, expires_at)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return cls(session_id, user_id, session_token, datetime.now(), expires_at)
    
    @classmethod
    def get_by_token(cls, session_token: str) -> Optional['UserSession']:
        """Get session by token"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, user_id, session_token, created_at, expires_at FROM user_sessions WHERE session_token = ?',
            (session_token,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(*row)
        return None
    
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        return datetime.now() < self.expires_at
    
    def delete(self):
        """Delete the session"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_sessions WHERE id = ?', (self.id,))
        conn.commit()
        conn.close() 