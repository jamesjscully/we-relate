import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class Subscription:
    """Subscription model for user billing"""
    
    def __init__(self, id=None, user_id=None, tier=None, status='active',
                 start_date=None, end_date=None, stripe_subscription_id=None,
                 created_at=None):
        self.id = id
        self.user_id = user_id
        self.tier = tier
        self.status = status
        self.start_date = start_date or datetime.now()
        self.end_date = end_date
        self.stripe_subscription_id = stripe_subscription_id
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def create(cls, user_id: int, tier: str, duration_months: int = 1,
               stripe_subscription_id: str = None) -> 'Subscription':
        """Create a new subscription"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30 * duration_months)
        
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Create subscriptions table if it doesn't exist
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
        
        cursor.execute(
            '''INSERT INTO subscriptions 
               (user_id, tier, start_date, end_date, stripe_subscription_id) 
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, tier, start_date, end_date, stripe_subscription_id)
        )
        
        subscription_id = cursor.lastrowid
        
        # Update user tier
        cursor.execute('UPDATE users SET tier = ? WHERE id = ?', (tier, user_id))
        
        conn.commit()
        conn.close()
        
        return cls.get_by_id(subscription_id)
    
    @classmethod
    def get_by_id(cls, subscription_id: int) -> Optional['Subscription']:
        """Get subscription by ID"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, user_id, tier, status, start_date, end_date, 
                      stripe_subscription_id, created_at 
               FROM subscriptions WHERE id = ?''',
            (subscription_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(*row)
        return None
    
    @classmethod
    def get_by_user_id(cls, user_id: int) -> List['Subscription']:
        """Get all subscriptions for a user"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, user_id, tier, status, start_date, end_date, 
                      stripe_subscription_id, created_at 
               FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC''',
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [cls(*row) for row in rows]
    
    @classmethod
    def get_active_by_user_id(cls, user_id: int) -> Optional['Subscription']:
        """Get active subscription for a user"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, user_id, tier, status, start_date, end_date, 
                      stripe_subscription_id, created_at 
               FROM subscriptions 
               WHERE user_id = ? AND status = 'active' AND end_date > ?
               ORDER BY created_at DESC LIMIT 1''',
            (user_id, datetime.now())
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(*row)
        return None
    
    def cancel(self):
        """Cancel the subscription"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE subscriptions SET status = ? WHERE id = ?',
            ('cancelled', self.id)
        )
        
        # Revert user to free tier if no other active subscriptions
        cursor.execute(
            '''SELECT COUNT(*) FROM subscriptions 
               WHERE user_id = ? AND status = 'active' AND end_date > ? AND id != ?''',
            (self.user_id, datetime.now(), self.id)
        )
        
        if cursor.fetchone()[0] == 0:
            cursor.execute('UPDATE users SET tier = ? WHERE id = ?', ('free', self.user_id))
        
        conn.commit()
        conn.close()
        
        self.status = 'cancelled'
    
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return (self.status == 'active' and 
                self.end_date and 
                datetime.now() < self.end_date)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tier': self.tier,
            'status': self.status,
            'start_date': self.start_date.isoformat() if isinstance(self.start_date, datetime) else self.start_date,
            'end_date': self.end_date.isoformat() if isinstance(self.end_date, datetime) else self.end_date,
            'stripe_subscription_id': self.stripe_subscription_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

class Payment:
    """Payment model for tracking transactions"""
    
    def __init__(self, id=None, user_id=None, amount=None, currency='usd',
                 status='pending', stripe_payment_intent_id=None,
                 description=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.currency = currency
        self.status = status
        self.stripe_payment_intent_id = stripe_payment_intent_id
        self.description = description
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def create(cls, user_id: int, amount: float, currency: str = 'usd',
               stripe_payment_intent_id: str = None, description: str = None) -> 'Payment':
        """Create a new payment record"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Create payments table if it doesn't exist
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
        
        cursor.execute(
            '''INSERT INTO payments 
               (user_id, amount, currency, stripe_payment_intent_id, description) 
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, amount, currency, stripe_payment_intent_id, description)
        )
        
        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return cls.get_by_id(payment_id)
    
    @classmethod
    def get_by_id(cls, payment_id: int) -> Optional['Payment']:
        """Get payment by ID"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, user_id, amount, currency, status, 
                      stripe_payment_intent_id, description, created_at 
               FROM payments WHERE id = ?''',
            (payment_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(*row)
        return None
    
    @classmethod
    def get_by_user_id(cls, user_id: int) -> List['Payment']:
        """Get all payments for a user"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT id, user_id, amount, currency, status, 
                      stripe_payment_intent_id, description, created_at 
               FROM payments WHERE user_id = ? ORDER BY created_at DESC''',
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [cls(*row) for row in rows]
    
    def update_status(self, status: str):
        """Update payment status"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE payments SET status = ? WHERE id = ?',
            (status, self.id)
        )
        conn.commit()
        conn.close()
        
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        } 