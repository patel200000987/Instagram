# number_info_bot.py
#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════
    🌟 PATEL INFO BOT - Premium Telegram Bot 🌟
    ═══════════════════════════════════════════════════════
    Using: osint | Credit System | Admin Panel
    Version: 1.0.0 (Premium Edition)
═══════════════════════════════════════════════════════════
"""

import os
import sys
import json
import time
import random
import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from functools import wraps
from collections import defaultdict
import re

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

# osint import
try:
    from patel_info import MobileInfo, quick_lookup, lookup
    VISHAI_AVAILABLE = True
except ImportError:
    VISHAI_AVAILABLE = False
    print("❌ osint not installed! Please install: pip install vishal-info")

import aiosqlite
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# 🎨 CONFIGURATION
# ============================================
class Config:
    """Bot Configuration"""
    
    # Bot Token from @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    # Admin IDs (comma separated in .env)
    ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
    
    # osint API Key
    API_KEY = os.getenv("API_KEY", "Errnkeor01")  # Default key from module
    
    # Database
    DB_PATH = "osint.db"
    
    # Credit System
    DEFAULT_CREDITS = 5  # Free credits for new users
    FREE_DAILY_CREDITS = 3  # Daily free credits
    REFERRAL_BONUS = 5  # Credits for referring a friend
    
    # Payment Configuration (UPI/QR)
    UPI_ID = os.getenv("UPI_ID", "your-upi@okhdfcbank")
    PAYMENT_QR = "https://ibb.co/gL7jcZJN"  # Replace with actual QR URL
    
    # Channels/Groups
    REQUIRED_CHANNEL = "@Black_Hats_Hackers"  # Channel to join for free credits
    SUPPORT_GROUP = "@Black_Hats_Support"
    
    # Rate Limiting
    RATE_LIMIT = 5  # Max requests per minute per user
    
    # Cache settings
    CACHE_TTL = 3600  # 1 hour
    
    # Timezone
    TIMEZONE = pytz.timezone("Asia/Kolkata")
    
    # Premium Plans (in INR)
    PLANS = {
        "basic": {
            "name": "📱 Basic",
            "credits": 50,
            "price": 50,
            "duration": 30,  # days
            "emoji": "🌟"
        },
        "pro": {
            "name": "⚡ Pro",
            "credits": 200,
            "price": 150,
            "duration": 30,
            "emoji": "💫"
        },
        "enterprise": {
            "name": "👑 Enterprise",
            "credits": 1000,
            "price": 500,
            "duration": 30,
            "emoji": "💎"
        }
    }

# ============================================
# 🎨 STYLISH FORMATTING
# ============================================
class Style:
    """Stylish formatting for Telegram messages"""
    
    # HTML Tags
    BOLD = "<b>"
    ITALIC = "<i>"
    CODE = "<code>"
    PRE = "<pre>"
    
    # Emojis
    EMOJI = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'phone': '📱',
        'person': '👤',
        'father': '👨',
        'address': '🏠',
        'circle': '🔄',
        'alternate': '📞',
        'id': '🆔',
        'email': '📧',
        'time': '⏰',
        'save': '💾',
        'search': '🔍',
        'star': '⭐',
        'heart': '❤️',
        'rocket': '🚀',
        'fire': '🔥',
        'sparkle': '✨',
        'telegram': '✈️',
        'crown': '👑',
        'diamond': '💎',
        'money': '💰',
        'credit': '💳',
        'gift': '🎁',
        'admin': '⚙️',
        'stats': '📊',
        'history': '📜',
        'settings': '🔧',
        'lock': '🔒',
        'unlock': '🔓',
        'bell': '🔔',
        'calendar': '📅',
        'clock': '🕐',
        'link': '🔗',
        'download': '⬇️',
        'upload': '⬆️',
        'refresh': '🔄',
        'ban': '🚫',
        'unban': '✅',
        'warn': '⚠️',
        'mute': '🔇',
        'unmute': '🔊',
        'vishal': '🕉️'
    }
    
    @staticmethod
    def bold(text: str) -> str:
        return f"<b>{text}</b>"
    
    @staticmethod
    def italic(text: str) -> str:
        return f"<i>{text}</i>"
    
    @staticmethod
    def code(text: str) -> str:
        return f"<code>{text}</code>"
    
    @staticmethod
    def pre(text: str) -> str:
        return f"<pre>{text}</pre>"
    
    @staticmethod
    def link(text: str, url: str) -> str:
        return f"<a href='{url}'>{text}</a>"

# ============================================
# 💾 DATABASE MANAGER
# ============================================
class Database:
    """Async SQLite Database Manager"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    credits INTEGER DEFAULT 0,
                    total_credits_used INTEGER DEFAULT 0,
                    total_searches INTEGER DEFAULT 0,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0,
                    premium_expiry TIMESTAMP,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    warning_count INTEGER DEFAULT 0,
                    notes TEXT
                )
            """)
            
            # Search history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    mobile_number TEXT,
                    search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    credits_used INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'success',
                    response_time REAL,
                    result_data TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount INTEGER,
                    credits INTEGER,
                    transaction_type TEXT,
                    payment_method TEXT,
                    transaction_id TEXT UNIQUE,
                    status TEXT DEFAULT 'pending',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_by INTEGER,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Daily credits tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_credits (
                    user_id INTEGER,
                    date DATE DEFAULT CURRENT_DATE,
                    credits_given INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, date)
                )
            """)
            
            # Cache table for osint results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vishal_cache (
                    mobile_number TEXT PRIMARY KEY,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Broadcasts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    sent_by INTEGER,
                    sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_sent INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending'
                )
            """)
            
            # Admin logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    target_user INTEGER,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Referrals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER UNIQUE,
                    bonus_claimed INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_id) REFERENCES users(user_id)
                )
            """)
            
            conn.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_user(self, user_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None,
                         referred_by: int = None) -> bool:
        """Create new user with default credits"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Generate unique referral code
                referral_code = f"VISHAI{user_id}{random.randint(1000,9999)}"
                
                # Check if user exists
                cursor = await db.execute(
                    "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
                )
                exists = await cursor.fetchone()
                
                if exists:
                    return True
                
                # Insert new user
                await db.execute("""
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, credits, referral_code, referred_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, Config.DEFAULT_CREDITS, referral_code, referred_by))
                
                # If referred, add referral bonus
                if referred_by:
                    # Check if referral already exists
                    cursor = await db.execute(
                        "SELECT id FROM referrals WHERE referred_id = ?", (user_id,)
                    )
                    ref_exists = await cursor.fetchone()
                    
                    if not ref_exists:
                        # Add to referrals table
                        await db.execute("""
                            INSERT INTO referrals (referrer_id, referred_id, bonus_claimed)
                            VALUES (?, ?, 0)
                        """, (referred_by, user_id))
                        
                        # Give bonus to referrer
                        await db.execute("""
                            UPDATE users SET credits = credits + ? 
                            WHERE user_id = ?
                        """, (Config.REFERRAL_BONUS, referred_by))
                        
                        # Mark bonus as claimed
                        await db.execute("""
                            UPDATE referrals SET bonus_claimed = 1 
                            WHERE referred_id = ?
                        """, (user_id,))
                
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return False
    
    async def update_credits(self, user_id: int, amount: int, 
                            transaction_type: str = "usage") -> bool:
        """Update user credits"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get current credits
                cursor = await db.execute(
                    "SELECT credits FROM users WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                
                if not row:
                    return False
                
                current_credits = row[0]
                new_credits = current_credits + amount
                
                if new_credits < 0:
                    return False
                
                # Update credits
                await db.execute(
                    "UPDATE users SET credits = ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (new_credits, user_id)
                )
                
                # Log transaction
                await db.execute("""
                    INSERT INTO transactions (user_id, amount, credits, transaction_type, status)
                    VALUES (?, ?, ?, ?, 'completed')
                """, (user_id, amount, amount, transaction_type))
                
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating credits: {e}")
            return False
    
    async def add_search_history(self, user_id: int, mobile: str, 
                                 credits_used: int = 1, result_data: str = None,
                                 status: str = 'success') -> bool:
        """Add search to history"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO search_history (user_id, mobile_number, credits_used, result_data, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, mobile, credits_used, result_data, status))
                
                # Update user stats
                if status == 'success':
                    await db.execute("""
                        UPDATE users 
                        SET total_searches = total_searches + 1,
                            total_credits_used = total_credits_used + ?
                        WHERE user_id = ?
                    """, (credits_used, user_id))
                
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding search history: {e}")
            return False
    
    async def get_daily_credits(self, user_id: int) -> int:
        """Get daily free credits given"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT credits_given FROM daily_credits 
                WHERE user_id = ? AND date = CURRENT_DATE
            """, (user_id,))
            row = await cursor.fetchone()
            return row[0] if row else 0
    
    async def add_daily_credits(self, user_id: int, credits: int) -> bool:
        """Add daily free credits"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO daily_credits (user_id, credits_given)
                    VALUES (?, ?)
                    ON CONFLICT(user_id, date) DO UPDATE SET
                    credits_given = credits_given + ?
                """, (user_id, credits, credits))
                
                # Add credits to user
                await db.execute(
                    "UPDATE users SET credits = credits + ? WHERE user_id = ?",
                    (credits, user_id)
                )
                
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding daily credits: {e}")
            return False
    
    async def get_vishal_cache(self, mobile: str) -> Optional[Dict]:
        """Get cached osint data"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT data FROM vishal_cache 
                WHERE mobile_number = ? 
                AND julianday('now') - julianday(timestamp) < ?
            """, (mobile, Config.CACHE_TTL / 86400))
            row = await cursor.fetchone()
            if row:
                return json.loads(row['data'])
            return None
    
    async def set_vishal_cache(self, mobile: str, data: Dict):
        """Cache osint data"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO vishal_cache (mobile_number, data)
                VALUES (?, ?)
            """, (mobile, json.dumps(data)))
            await db.commit()
    
    async def get_all_users(self, banned_only: bool = False) -> List[Dict]:
        """Get all users or banned users"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM users"
            if banned_only:
                query += " WHERE is_banned = 1"
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_stats(self) -> Dict:
        """Get bot statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Total users
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = (await cursor.fetchone())[0]
            
            # Active users (last 24h)
            cursor = await db.execute("""
                SELECT COUNT(DISTINCT user_id) FROM search_history 
                WHERE search_time > datetime('now', '-1 day')
            """)
            stats['active_users'] = (await cursor.fetchone())[0]
            
            # Total searches
            cursor = await db.execute("SELECT COUNT(*) FROM search_history")
            stats['total_searches'] = (await cursor.fetchone())[0]
            
            # Total credits used
            cursor = await db.execute("SELECT SUM(total_credits_used) FROM users")
            stats['total_credits'] = (await cursor.fetchone())[0] or 0
            
            # Successful searches
            cursor = await db.execute("""
                SELECT COUNT(*) FROM search_history WHERE status = 'success'
            """)
            stats['successful'] = (await cursor.fetchone())[0]
            
            # Failed searches
            cursor = await db.execute("""
                SELECT COUNT(*) FROM search_history WHERE status = 'failed'
            """)
            stats['failed'] = (await cursor.fetchone())[0]
            
            # Total earnings (estimated from transactions)
            cursor = await db.execute("""
                SELECT SUM(amount) FROM transactions WHERE status = 'completed'
            """)
            stats['total_earnings'] = (await cursor.fetchone())[0] or 0
            
            return stats
    
    async def get_referrals(self, user_id: int) -> Dict:
        """Get referral statistics for user"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total referrals
            cursor = await db.execute("""
                SELECT COUNT(*) FROM referrals WHERE referrer_id = ?
            """, (user_id,))
            total = (await cursor.fetchone())[0]
            
            # Bonus earned
            cursor = await db.execute("""
                SELECT COUNT(*) * ? FROM referrals 
                WHERE referrer_id = ? AND bonus_claimed = 1
            """, (Config.REFERRAL_BONUS, user_id))
            bonus = (await cursor.fetchone())[0] or 0
            
            return {'total': total, 'bonus': bonus}

# ============================================
# 🔍 VISHAI-INFO SERVICE
# ============================================
class VishalInfoService:
    """Handle osint operations"""
    
    def __init__(self, api_key: str, db: Database):
        self.api_key = api_key
        self.db = db
        self.mobile_info = None
        
        # Initialize MobileInfo if module available
        if VISHAI_AVAILABLE:
            self.mobile_info = MobileInfo(api_key=self.api_key)
    
    async def lookup(self, mobile: str) -> Optional[Dict]:
        """Lookup mobile number using database"""
        try:
            # Check cache first
            cached = await self.db.get_vishal_cache(mobile)
            if cached:
                return cached
            
            if not VISHAI_AVAILABLE:
                return {"error": "osint not installed"}
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Use quick_lookup or MobileInfo
            try:
                # Try quick_lookup first (faster)
                result = await loop.run_in_executor(
                    None, quick_lookup, mobile
                )
            except:
                # Fallback to MobileInfo class
                result = await loop.run_in_executor(
                    None, lambda: self.mobile_info.get_info(mobile)
                )
            
            # Cache the result
            if result:
                await self.db.set_vishal_cache(mobile, result)
            
            return result
            
        except Exception as e:
            logging.error(f"osint lookup error: {e}")
            return None
    
    def format_result(self, data: Dict, mobile: str) -> str:
        """Format osint result beautifully"""
        if not data:
            return f"{Style.EMOJI['error']} No information found for {mobile}"
        
        if isinstance(data, dict) and 'error' in data:
            return f"{Style.EMOJI['error']} {data['error']}"
        
        result = f"""
{Style.EMOJI['vishal']}{Style.bold(' VISHAI INFO RESULTS ')}{Style.EMOJI['vishal']}
╔══════════════════════════════════════╗
║  Number: {Style.code(mobile)}               
╚══════════════════════════════════════╝

"""
        if isinstance(data, list):
            for idx, record in enumerate(data, 1):
                result += f"""
{Style.EMOJI['diamond']} {Style.bold(f'Record #{idx}')}
┌──────────────────────────────────
"""
                # Personal Info
                if record.get('name'):
                    result += f"│ {Style.EMOJI['person']} Name    : {Style.bold(record['name'])}\n"
                if record.get('fname'):
                    result += f"│ {Style.EMOJI['father']} Father  : {record['fname']}\n"
                
                # Address
                if record.get('address'):
                    addr = self._format_address(record['address'])
                    result += f"│ {Style.EMOJI['address']} Address : {addr}\n"
                
                # Additional Info
                if record.get('circle'):
                    result += f"│ {Style.EMOJI['circle']} Circle  : {record['circle']}\n"
                if record.get('alt'):
                    result += f"│ {Style.EMOJI['alternate']} Alt No. : {record['alt']}\n"
                if record.get('id'):
                    result += f"│ {Style.EMOJI['id']} ID      : {record['id']}\n"
                if record.get('email'):
                    result += f"│ {Style.EMOJI['email']} Email   : {record['email']}\n"
                
                result += "└──────────────────────────────────\n"
        else:
            # Single record
            result += """
┌──────────────────────────────────
"""
            if data.get('name'):
                result += f"│ {Style.EMOJI['person']} Name    : {Style.bold(data['name'])}\n"
            if data.get('fname'):
                result += f"│ {Style.EMOJI['father']} Father  : {data['fname']}\n"
            if data.get('address'):
                addr = self._format_address(data['address'])
                result += f"│ {Style.EMOJI['address']} Address : {addr}\n"
            if data.get('circle'):
                result += f"│ {Style.EMOJI['circle']} Circle  : {data['circle']}\n"
            if data.get('alt'):
                result += f"│ {Style.EMOJI['alternate']} Alt No. : {data['alt']}\n"
            if data.get('id'):
                result += f"│ {Style.EMOJI['id']} ID      : {data['id']}\n"
            if data.get('email'):
                result += f"│ {Style.EMOJI['email']} Email   : {data['email']}\n"
            
            result += "└──────────────────────────────────\n"
        
        # Footer
        result += f"""
{Style.EMOJI['time']} Time: {datetime.now(Config.TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}
{Style.EMOJI['telegram']} Join: {Config.REQUIRED_CHANNEL}
{Style.EMOJI['vishal']} Powered by osint
"""
        return result
    
    def _format_address(self, address: str) -> str:
        """Format address nicely"""
        if not address or address == "N/A":
            return "N/A"
        # Replace separators
        formatted = address.replace('!', ' → ').replace('!!', ' → ').replace('!!!', ' → ')
        # Truncate if too long
        if len(formatted) > 100:
            formatted = formatted[:97] + "..."
        return formatted

# ============================================
# 🔐 RATE LIMITER
# ============================================
class RateLimiter:
    """Rate limiting for user requests"""
    
    def __init__(self, max_requests: int = Config.RATE_LIMIT, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make request"""
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        user_requests = [req_time for req_time in user_requests 
                        if now - req_time < self.window]
        self.requests[user_id] = user_requests
        
        if len(user_requests) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: int) -> int:
        """Get remaining requests for user"""
        now = time.time()
        user_requests = [req_time for req_time in self.requests[user_id] 
                        if now - req_time < self.window]
        return max(0, self.max_requests - len(user_requests))

# ============================================
# 🎨 UI COMPONENTS
# ============================================
class UIComponents:
    """Stylish UI components"""
    
    @staticmethod
    def main_menu(user_data: Dict = None) -> InlineKeyboardMarkup:
        """Create main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton(f"{Style.EMOJI['search']} Search Number", callback_data="search"),
                InlineKeyboardButton(f"{Style.EMOJI['credit']} My Credits", callback_data="credits")
            ],
            [
                InlineKeyboardButton(f"{Style.EMOJI['history']} History", callback_data="history"),
                InlineKeyboardButton(f"{Style.EMOJI['gift']} Free Credits", callback_data="free")
            ],
            [
                InlineKeyboardButton(f"{Style.EMOJI['money']} Buy Credits", callback_data="buy"),
                InlineKeyboardButton(f"{Style.EMOJI['stats']} My Stats", callback_data="stats")
            ],
            [
                InlineKeyboardButton(f"{Style.EMOJI['telegram']} Join Channel", url=f"https://t.me/{Config.REQUIRED_CHANNEL[1:]}"),
                InlineKeyboardButton(f"{Style.EMOJI['settings']} Help", callback_data="help")
            ]
        ]
        
        # Add referral button
        keyboard.append([
            InlineKeyboardButton(f"{Style.EMOJI['gift']} Refer & Earn", callback_data="refer")
        ])
        
        # Add admin panel if user is admin
        if user_data and user_data.get('is_admin'):
            keyboard.append([InlineKeyboardButton(f"{Style.EMOJI['admin']} Admin Panel", callback_data="admin")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Create admin menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Dashboard", callback_data="admin_dashboard"),
                InlineKeyboardButton("👥 Users", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("💰 Credits", callback_data="admin_credits"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton("🚫 Ban/Unban", callback_data="admin_ban"),
                InlineKeyboardButton("📜 Logs", callback_data="admin_logs")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"),
                InlineKeyboardButton("🔙 Back", callback_data="back_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def buy_credits_menu() -> InlineKeyboardMarkup:
        """Create buy credits keyboard"""
        keyboard = []
        for plan_id, plan in Config.PLANS.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{plan['emoji']} {plan['name']} - {plan['credits']} Credits (₹{plan['price']})",
                    callback_data=f"buy_{plan_id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)

# ============================================
# 🤖 MAIN BOT CLASS
# ============================================
class VishalInfoBot:
    """Main bot application using osint"""
    
    def __init__(self):
        self.db = Database(Config.DB_PATH)
        self.vishal_service = VishalInfoService(Config.API_KEY, self.db)
        self.rate_limiter = RateLimiter()
        self.ui = UIComponents()
        
        # Conversation states
        self.WAITING_NUMBER, self.WAITING_BROADCAST, self.WAITING_USER_ID = range(3)
        
        # Setup logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
        # Check 
        if not VISHAI_AVAILABLE:
            logging.error("osint not installed!")
            print("""
╔══════════════════════════════════════════╗
║  ❌ osint not installed!   ║
╠══════════════════════════════════════════╣
║  Install using:                          ║
║  pip install osint                 ║
║                                           ║
║  Or from source:                          ║
║  pip install git+https://github.com/     ║
║  vishal-info/vishal-info.git              ║
╚══════════════════════════════════════════╝
            """)
    
    # ============================================
    # 🔐 DECORATORS
    # ============================================
    def admin_only(func):
        """Decorator to restrict to admins only"""
        @wraps(func)
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            if user.id not in Config.ADMIN_IDS:
                await update.message.reply_text(
                    f"{Style.EMOJI['error']} This command is for admins only!"
                )
                return
            return await func(self, update, context, *args, **kwargs)
        return wrapper
    
    def require_credits(credits_needed: int = 1):
        """Decorator to check if user has enough credits"""
        def decorator(func):
            @wraps(func)
            async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                user = update.effective_user
                
                # Check rate limit
                if not self.rate_limiter.is_allowed(user.id):
                    remaining = self.rate_limiter.get_remaining(user.id)
                    await update.message.reply_text(
                        f"{Style.EMOJI['warning']} Rate limit exceeded!\n"
                        f"Please wait {remaining} seconds."
                    )
                    return
                
                # Get user from database
                db_user = await self.db.get_user(user.id)
                if not db_user:
                    await self.db.create_user(user.id, user.username, user.first_name, user.last_name)
                    db_user = await self.db.get_user(user.id)
                
                # Check ban status
                if db_user.get('is_banned'):
                    await update.message.reply_text(
                        f"{Style.EMOJI['ban']} You are banned from using this bot!"
                    )
                    return
                
                # Check credits
                if db_user['credits'] < credits_needed:
                    await update.message.reply_text(
                        f"{Style.EMOJI['error']} Insufficient credits!\n"
                        f"You need {credits_needed} credits.\n"
                        f"Your balance: {db_user['credits']} credits\n\n"
                        f"Get free credits: /free\n"
                        f"Buy credits: /buy",
                        reply_markup=self.ui.buy_credits_menu()
                    )
                    return
                
                # Add user to context for use in function
                context.user_data['db_user'] = db_user
                return await func(self, update, context, *args, **kwargs)
            return wrapper
        return decorator
    
    # ============================================
    # 🚀 COMMAND HANDLERS
    # ============================================
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        
        # Check for referral
        referred_by = None
        if context.args and len(context.args) > 0:
            try:
                # Extract referrer ID from referral code
                ref_code = context.args[0]
                if ref_code.startswith('ref_'):
                    referred_by = int(ref_code.replace('ref_', ''))
            except:
                pass
        
        # Create user in database if not exists
        db_user = await self.db.get_user(user.id)
        if not db_user:
            await self.db.create_user(
                user.id, user.username, user.first_name, user.last_name,
                referred_by=referred_by
            )
            db_user = await self.db.get_user(user.id)
            
            # Send welcome message to new users
            welcome_text = f"""
{Style.EMOJI['vishal']}{Style.bold(' WELCOME TO VISHAI INFO BOT ')}{Style.EMOJI['vishal']}
╔══════════════════════════════════════╗
║  📱 Indian Mobile Number Lookup     ║
║  👤 Name, Father's Name              ║
║  🏠 Complete Address                 ║
║  📞 Alternate Numbers                ║
║  🆔 ID Information                   ║
║  📧 Email Details                    ║
╚══════════════════════════════════════╝

{Style.EMOJI['gift']} You've received {Style.bold(f'{Config.DEFAULT_CREDITS} free credits!')}

{Style.bold('🎁 Get More Credits:')}
• /free - Get daily free credits
• /buy - Purchase credits
• /refer - Refer friends (earn {Config.REFERRAL_BONUS} credits each)

{Style.bold('🔍 How to Use:')}
Simply send me a 10-digit mobile number
Example: <code>9936265050</code>

{Style.EMOJI['telegram']} Join: {Config.REQUIRED_CHANNEL}
"""
        else:
            welcome_text = f"""
{Style.EMOJI['heart']} {Style.bold('Welcome Back!')} {user.first_name}

{Style.EMOJI['credit']} Your Balance: {Style.bold(f'{db_user["credits"]} credits')}
{Style.EMOJI['search']} Total Searches: {Style.bold(db_user["total_searches"])}

{Style.bold('Quick Actions:')}
🔍 Send a number to search
💰 /buy - Buy more credits
🎁 /free - Get free credits
📊 /stats - Your statistics
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=self.ui.main_menu(db_user)
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = f"""
{Style.EMOJI['info']}{Style.bold(' VISHAI INFO BOT - HELP ')}{Style.EMOJI['info']}
╔══════════════════════════════════════╗
║           COMMANDS LIST              ║
╚══════════════════════════════════════╝

{Style.bold('📱 Basic Commands:')}
/start - Start the bot
/help - Show this help
/credits - Check your credits
/history - View search history
/stats - Your statistics

{Style.bold('💰 Credit Commands:')}
/free - Get daily free credits
/buy - Buy more credits
/refer - Refer friends (earn {Config.REFERRAL_BONUS} credits)

{Style.bold('🔍 How to Search:')}
Simply send any 10-digit Indian mobile number
Example: <code>9876543210</code>

{Style.bold('⚡ Features:')}
• ✅ Fast lookup using osint
• ✅ Accurate Indian mobile data
• ✅ Name, Father's name, Address
• ✅ Alternate numbers, Email
• ✅ Circle/Operator info
• ✅ Cache system for faster results

{Style.bold('📞 Support:')}
Channel: {Config.REQUIRED_CHANNEL}
Group: {Config.SUPPORT_GROUP}

{Style.EMOJI['vishal']} Powered by osint
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    @require_credits(0)
    async def credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check credits command"""
        db_user = context.user_data.get('db_user')
        
        # Get daily credits info
        daily_credits = await self.db.get_daily_credits(update.effective_user.id)
        
        credits_text = f"""
{Style.EMOJI['credit']}{Style.bold(' YOUR CREDIT BALANCE ')}{Style.EMOJI['credit']}
╔══════════════════════════════════════╗
║  💰 Available: {Style.bold(str(db_user['credits']).rjust(10))}     ║
║  📊 Total Used: {Style.bold(str(db_user['total_credits_used']).rjust(8))}     ║
║  🔍 Searches: {Style.bold(str(db_user['total_searches']).rjust(9))}     ║
║  🎁 Daily Used: {Style.bold(str(daily_credits) + '/' + str(Config.FREE_DAILY_CREDITS)).rjust(7)}     ║
╚══════════════════════════════════════╝

{Style.bold('Get More Credits:')}
• /free - Daily free credits
• /buy - Purchase credits
• /refer - Refer friends
"""
        await update.message.reply_text(
            credits_text,
            parse_mode=ParseMode.HTML,
            reply_markup=self.ui.main_menu(db_user)
        )
    
    async def free_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get daily free credits"""
        user_id = update.effective_user.id
        
        # Check if already claimed today
        daily_credits = await self.db.get_daily_credits(user_id)
        
        if daily_credits >= Config.FREE_DAILY_CREDITS:
            await update.message.reply_text(
                f"{Style.EMOJI['warning']} You've already claimed your daily free credits!\n"
                f"Come back tomorrow for more."
            )
            return
        
        # Check if user joined required channel
        try:
            member = await context.bot.get_chat_member(
                Config.REQUIRED_CHANNEL, user_id
            )
            if member.status in ['left', 'kicked']:
                await update.message.reply_text(
                    f"{Style.EMOJI['warning']} Please join our channel first!\n\n"
                    f"👉 {Config.REQUIRED_CHANNEL}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            f"{Style.EMOJI['telegram']} Join Channel",
                            url=f"https://t.me/{Config.REQUIRED_CHANNEL[1:]}"
                        )
                    ]])
                )
                return
        except:
            # Channel might be private or error, allow anyway
            pass
        
        # Give free credits
        remaining = Config.FREE_DAILY_CREDITS - daily_credits
        await self.db.add_daily_credits(user_id, remaining)
        
        # Get updated user
        db_user = await self.db.get_user(user_id)
        
        await update.message.reply_text(
            f"{Style.EMOJI['gift']}{Style.bold(' FREE CREDITS CLAIMED! ')}{Style.EMOJI['gift']}\n\n"
            f"✅ You received {Style.bold(remaining)} free credits!\n"
            f"💰 New Balance: {Style.bold(db_user['credits'])} credits\n\n"
            f"🎁 Come back tomorrow for more!",
            parse_mode=ParseMode.HTML
        )
    
    async def buy_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show credit plans"""
        plans_text = f"""
{Style.EMOJI['money']}{Style.bold(' BUY CREDITS ')}{Style.EMOJI['money']}
╔══════════════════════════════════════╗
║         AVAILABLE PLANS              ║
╚══════════════════════════════════════╝

"""
        for plan_id, plan in Config.PLANS.items():
            plans_text += f"""
{plan['emoji']} {Style.bold(plan['name'])}:
   • {plan['credits']} Credits
   • ₹{plan['price']} only
   • Valid for {plan['duration']} days
"""
        
        plans_text += f"""
{Style.EMOJI['info']} Click below to purchase
Payment via UPI: <code>{Config.UPI_ID}</code>
"""
        
        await update.message.reply_text(
            plans_text,
            parse_mode=ParseMode.HTML,
            reply_markup=self.ui.buy_credits_menu()
        )
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show search history"""
        user_id = update.effective_user.id
        
        async with aiosqlite.connect(Config.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT mobile_number, search_time, status 
                FROM search_history 
                WHERE user_id = ? 
                ORDER BY search_time DESC 
                LIMIT 10
            """, (user_id,))
            rows = await cursor.fetchall()
        
        if not rows:
            await update.message.reply_text(
                f"{Style.EMOJI['info']} No search history yet.\n"
                f"Send a number to start searching!"
            )
            return
        
        history_text = f"""
{Style.EMOJI['history']}{Style.bold(' RECENT SEARCHES ')}{Style.EMOJI['history']}
╔══════════════════════════════════════╗
║         LAST 10 SEARCHES             ║
╚══════════════════════════════════════╝

"""
        for i, row in enumerate(rows, 1):
            time_str = datetime.fromisoformat(row['search_time']).strftime('%H:%M %d/%m')
            status_emoji = Style.EMOJI['success'] if row['status'] == 'success' else Style.EMOJI['error']
            history_text += f"{i}. {status_emoji} <code>{row['mobile_number']}</code>\n   🕐 {time_str}\n\n"
        
        await update.message.reply_text(history_text, parse_mode=ParseMode.HTML)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        user_id = update.effective_user.id
        db_user = await self.db.get_user(user_id)
        
        # Get today's searches
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) FROM search_history 
                WHERE user_id = ? AND date(search_time) = CURRENT_DATE
            """, (user_id,))
            today_searches = (await cursor.fetchone())[0]
        
        # Get referral stats
        referrals = await self.db.get_referrals(user_id)
        
        stats_text = f"""
{Style.EMOJI['stats']}{Style.bold(' YOUR STATISTICS ')}{Style.EMOJI['stats']}
╔══════════════════════════════════════╗
║         USER DASHBOARD               ║
╚══════════════════════════════════════╝

👤 Name: {Style.bold(update.effective_user.first_name)}
🆔 ID: <code>{user_id}</code>

💰 Credits: {Style.bold(db_user['credits'])}
📊 Total Used: {Style.bold(db_user['total_credits_used'])}
🔍 Total Searches: {Style.bold(db_user['total_searches'])}
📅 Today: {Style.bold(today_searches)} searches

{Style.EMOJI['gift']} Referrals: {Style.bold(referrals['total'])}
🎁 Bonus Earned: {Style.bold(referrals['bonus'])} credits

📈 Success Rate: {Style.bold(f'{(db_user["total_searches"] / db_user["total_credits_used"] * 100) if db_user["total_credits_used"] > 0 else 0:.1f}%')}
🎉 Joined: {Style.bold(datetime.fromisoformat(db_user['join_date']).strftime('%d %b %Y'))}
"""
        await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)
    
    async def refer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Referral command"""
        user_id = update.effective_user.id
        db_user = await self.db.get_user(user_id)
        
        # Get referral stats
        referrals = await self.db.get_referrals(user_id)
        
        # Create referral link
        bot_username = (await context.bot.get_me()).username
        refer_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        
        refer_text = f"""
{Style.EMOJI['gift']}{Style.bold(' REFER & EARN ')}{Style.EMOJI['gift']}
╔══════════════════════════════════════╗
║    EARN {Config.REFERRAL_BONUS} CREDITS PER FRIEND!    ║
╚══════════════════════════════════════╝

{Style.bold('Your Referral Stats:')}
👥 Total Referrals: {referrals['total']}
💰 Bonus Earned: {referrals['bonus']} credits

{Style.bold('Your Referral Link:')}
<code>{refer_link}</code>

{Style.bold('How it works:')}
1. Share this link with friends
2. They start the bot using your link
3. You get {Config.REFERRAL_BONUS} credits instantly
4. They get {Config.DEFAULT_CREDITS} free credits

{Style.bold('Share via:')}
🔗 Copy link and share anywhere!
"""
        keyboard = [
            [InlineKeyboardButton("📤 Share Link", switch_inline_query=f"Join @{bot_username} and get free credits!")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ]
        
        await update.message.reply_text(
            refer_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # ============================================
    # 📱 NUMBER HANDLER
    # ============================================
    @require_credits(1)
    async def handle_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle mobile number input"""
        number = update.message.text.strip()
        user_id = update.effective_user.id
        db_user = context.user_data.get('db_user')
        
        # Validate number
        valid_number = self.validate_mobile(number)
        if not valid_number:
            await update.message.reply_text(
                f"{Style.EMOJI['error']} Invalid mobile number!\n\n"
                f"Please enter a valid 10-digit Indian mobile number.\n"
                f"Example: <code>9936265050</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Send typing action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Send searching message
        search_msg = await update.message.reply_text(
            f"{Style.EMOJI['search']} Searching for {valid_number}...\n"
            f"{Style.EMOJI['vishal']} Using osint...",
            parse_mode=ParseMode.HTML
        )
        
        # Deduct credit
        await self.db.update_credits(user_id, -1, "usage")
        
        # Perform lookup
        start_time = time.time()
        result = await self.vishal_service.lookup(valid_number)
        response_time = time.time() - start_time
        
        # Delete searching message
        await search_msg.delete()
        
        if result and not isinstance(result, dict) or (isinstance(result, dict) and 'error' not in result):
            # Save to history
            await self.db.add_search_history(
                user_id, valid_number, 1, 
                json.dumps(result)[:500]  # Store preview
            )
            
            # Format and send result
            formatted_result = self.vishal_service.format_result(result, valid_number)
            
            # Add credit info
            remaining_credits = db_user['credits'] - 1
            formatted_result += f"\n{Style.EMOJI['credit']} Credits used: 1 | Remaining: {remaining_credits}"
            
            await update.message.reply_text(
                formatted_result,
                parse_mode=ParseMode.HTML
            )
            
            # Ask for review/feedback (20% chance)
            if random.random() < 0.2:
                await update.message.reply_text(
                    f"{Style.EMOJI['heart']} Enjoying Vishal Info Bot? Share with friends and earn free credits!\n"
                    f"Use /refer to get your referral link."
                )
        else:
            # Save failed search
            await self.db.add_search_history(user_id, valid_number, 1, status='failed')
            
            # Refund credit for failed search
            await self.db.update_credits(user_id, 1, "refund")
            
            error_msg = result.get('error', 'No information found') if isinstance(result, dict) else 'No information found'
            
            await update.message.reply_text(
                f"{Style.EMOJI['error']} {error_msg} for {valid_number}\n\n"
                f"Possible reasons:\n"
                f"• Number not in osint database\n"
                f"• API temporary unavailable\n"
                f"• Invalid number\n\n"
                f"Your credit has been refunded.\n"
                f"Current balance: {db_user['credits']} credits"
            )
    
    def validate_mobile(self, number: str) -> Optional[str]:
        """Validate Indian mobile number"""
        # Remove any non-digit characters
        clean = ''.join(filter(str.isdigit, number))
        
        # Check length and format
        if len(clean) == 10:
            # Check if starts with valid Indian mobile prefixes (6-9)
            if clean[0] in '6789':
                return clean
        elif len(clean) == 11 and clean.startswith('0'):
            if clean[1] in '6789':
                return clean[1:]
        elif len(clean) == 12 and clean.startswith('91'):
            if clean[2] in '6789':
                return clean[2:]
        return None
    
    # ============================================
    # 👑 ADMIN COMMANDS
    # ============================================
    @admin_only
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin panel command"""
        stats = await self.db.get_stats()
        
        admin_text = f"""
{Style.EMOJI['admin']}{Style.bold(' VISHAI INFO - ADMIN PANEL ')}{Style.EMOJI['admin']}
╔══════════════════════════════════════╗
║         BOT STATISTICS               ║
╚══════════════════════════════════════╝

{Style.bold('📊 Bot Statistics:')}
👥 Total Users: {Style.bold(stats['total_users'])}
📈 Active Today: {Style.bold(stats['active_users'])}
🔍 Total Searches: {Style.bold(stats['total_searches'])}
💰 Credits Used: {Style.bold(stats['total_credits'])}
✅ Successful: {Style.bold(stats['successful'])}
❌ Failed: {Style.bold(stats['failed'])}
💵 Earnings: ₹{Style.bold(stats['total_earnings'])}

{Style.bold('⚙️ System Info:')}
🤖 osint: {'✅ Available' if VISHAI_AVAILABLE else '❌ Not Installed'}
💾 Database: SQLite
⏰ Time: {datetime.now(Config.TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}
"""
        await update.message.reply_text(
            admin_text,
            parse_mode=ParseMode.HTML,
            reply_markup=self.ui.admin_menu()
        )
    
    @admin_only
    async def admin_broadcast_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start broadcast conversation"""
        await update.message.reply_text(
            f"{Style.EMOJI['bell']} Send me the message to broadcast to all users:\n\n"
            f"<i>You can use HTML formatting</i>\n"
            f"<i>Type /cancel to cancel</i>",
            parse_mode=ParseMode.HTML
        )
        return self.WAITING_BROADCAST
    
    @admin_only
    async def admin_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast message"""
        message = update.message.text
        
        if message == '/cancel':
            await update.message.reply_text("❌ Broadcast cancelled.")
            return ConversationHandler.END
        
        # Confirm broadcast
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Send", callback_data="broadcast_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
            ]
        ]
        
        context.user_data['broadcast_message'] = message
        
        # Get preview
        preview = message[:200] + "..." if len(message) > 200 else message
        
        await update.message.reply_text(
            f"{Style.EMOJI['warning']} Are you sure you want to broadcast this message?\n\n"
            f"{Style.bold('Preview:')}\n{preview}\n\n"
            f"<i>This will be sent to all {stats['total_users']} users.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    async def admin_broadcast_execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute broadcast"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "broadcast_confirm":
            await query.edit_message_text(
                f"{Style.EMOJI['bell']} Broadcasting started...\n\n"
                f"This may take a while. I'll notify you when complete."
            )
            
            # Get all users
            users = await self.db.get_all_users()
            message = context.user_data.get('broadcast_message', '')
            
            sent = 0
            failed = 0
            
            for user in users:
                try:
                    await context.bot.send_message(
                        user['user_id'],
                        message,
                        parse_mode=ParseMode.HTML
                    )
                    sent += 1
                    await asyncio.sleep(0.05)  # Rate limiting
                except Exception as e:
                    failed += 1
                    logging.error(f"Broadcast failed to {user['user_id']}: {e}")
                
                # Update progress every 50 users
                if sent % 50 == 0:
                    await context.bot.send_message(
                        update.effective_user.id,
                        f"Progress: {sent} users processed..."
                    )
            
            # Log broadcast
            async with aiosqlite.connect(Config.DB_PATH) as db:
                await db.execute("""
                    INSERT INTO broadcasts (message, sent_by, total_sent, total_failed, status)
                    VALUES (?, ?, ?, ?, 'completed')
                """, (message, update.effective_user.id, sent, failed))
                await db.commit()
            
            await context.bot.send_message(
                update.effective_user.id,
                f"{Style.EMOJI['success']} Broadcast completed!\n\n"
                f"✅ Sent: {sent}\n"
                f"❌ Failed: {failed}"
            )
        else:
            await query.edit_message_text("❌ Broadcast cancelled.")
    
    @admin_only
    async def admin_add_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add credits to user"""
        try:
            # Format: /addcredits user_id amount
            args = context.args
            if len(args) != 2:
                await update.message.reply_text(
                    f"{Style.EMOJI['error']} Usage: /addcredits <user_id> <amount>"
                )
                return
            
            user_id = int(args[0])
            amount = int(args[1])
            
            # Check if user exists
            user = await self.db.get_user(user_id)
            if not user:
                await update.message.reply_text(f"{Style.EMOJI['error']} User not found!")
                return
            
            # Add credits
            await self.db.update_credits(user_id, amount, "admin_add")
            
            # Log action
            async with aiosqlite.connect(Config.DB_PATH) as db:
                await db.execute("""
                    INSERT INTO admin_logs (admin_id, action, target_user, details)
                    VALUES (?, 'add_credits', ?, ?)
                """, (update.effective_user.id, user_id, f"Added {amount} credits"))
                await db.commit()
            
            await update.message.reply_text(
                f"{Style.EMOJI['success']} Added {amount} credits to user {user_id}\n"
                f"New balance: {user['credits'] + amount} credits"
            )
            
            # Notify user
            try:
                await context.bot.send_message(
                    user_id,
                    f"{Style.EMOJI['gift']} You received {amount} free credits from admin!\n"
                    f"New balance: {user['credits'] + amount} credits\n\n"
                    f"Use /credits to check your balance."
                )
            except:
                pass
                
        except Exception as e:
            await update.message.reply_text(f"{Style.EMOJI['error']} Error: {e}")
    
    @admin_only
    async def admin_remove_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove credits from user"""
        try:
            args = context.args
            if len(args) != 2:
                await update.message.reply_text(
                    f"{Style.EMOJI['error']} Usage: /removecredits <user_id> <amount>"
                )
                return
            
            user_id = int(args[0])
            amount = int(args[1])
            
            user = await self.db.get_user(user_id)
            if not user:
                await update.message.reply_text(f"{Style.EMOJI['error']} User not found!")
                return
            
            # Remove credits (negative amount)
            await self.db.update_credits(user_id, -amount, "admin_remove")
            
            # Log action
            async with aiosqlite.connect(Config.DB_PATH) as db:
                await db.execute("""
                    INSERT INTO admin_logs (admin_id, action, target_user, details)
                    VALUES (?, 'remove_credits', ?, ?)
                """, (update.effective_user.id, user_id, f"Removed {amount} credits"))
                await db.commit()
            
            await update.message.reply_text(
                f"{Style.EMOJI['success']} Removed {amount} credits from user {user_id}\n"
                f"New balance: {user['credits'] - amount} credits"
            )
            
        except Exception as e:
            await update.message.reply_text(f"{Style.EMOJI['error']} Error: {e}")
    
    @admin_only
    async def admin_ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban user"""
        try:
            args = context.args
            if len(args) < 1:
                await update.message.reply_text(
                    f"{Style.EMOJI['error']} Usage: /ban <user_id> <reason>"
                )
                return
            
            user_id = int(args[0])
            reason = ' '.join(args[1:]) if len(args) > 1 else "No reason provided"
            
            # Check if user exists
            user = await self.db.get_user(user_id)
            if not user:
                await update.message.reply_text(f"{Style.EMOJI['error']} User not found!")
                return
            
            async with aiosqlite.connect(Config.DB_PATH) as db:
                await db.execute(
                    "UPDATE users SET is_banned = 1, notes = ? WHERE user_id = ?",
                    (f"Banned: {reason}", user_id)
                )
                await db.commit()
            
            await update.message.reply_text(
                f"{Style.EMOJI['ban']} User {user_id} has been banned.\n"
                f"Reason: {reason}"
            )
            
            # Log action
            async with aiosqlite.connect(Config.DB_PATH) as db:
                await db.execute("""
                    INSERT INTO admin_logs (admin_id, action, target_user, details)
                    VALUES (?, 'ban', ?, ?)
                """, (update.effective_user.id, user_id, reason))
                await db.commit()
            
            # Notify user
            try:
                await context.bot.send_message(
                    user_id,
                    f"{Style.EMOJI['ban']} You have been banned from using Vishal Info Bot.\n"
                    f"Reason: {reason}\n\n"
                    f"Contact @Black_Hats_Support for appeal."
                )
            except:
                pass
                
        except Exception as e:
            await update.message.reply_text(f"{Style.EMOJI['error']} Error: {e}")
    
    @admin_only
    async def admin_unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban user"""
        try:
            user_id = int(context.args[0]) if context.args else None
            if not user_id:
                await update.message.reply_text(f"{Style.EMOJI['error']} Usage: /unban <user_id>")
                return
            
            async with aiosqlite.connect(Config.DB_PATH) as db:
                await db.execute(
                    "UPDATE users SET is_banned = 0 WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
            
            await update.message.reply_text(
                f"{Style.EMOJI['unlock']} User {user_id} has been unbanned."
            )
            
            # Log action
            async with aiosqlite.connect(Config.DB_PATH) as db:
                await db.execute("""
                    INSERT INTO admin_logs (admin_id, action, target_user, details)
                    VALUES (?, 'unban', ?, 'User unbanned')
                """, (update.effective_user.id, user_id))
                await db.commit()
            
            # Notify user
            try:
                await context.bot.send_message(
                    user_id,
                    f"{Style.EMOJI['unlock']} You have been unbanned from Vishal Info Bot!\n"
                    f"You can now use the bot again."
                )
            except:
                pass
                
        except Exception as e:
            await update.message.reply_text(f"{Style.EMOJI['error']} Error: {e}")
    
    @admin_only
    async def admin_users_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List users"""
        users = await self.db.get_all_users()
        
        text = f"""
{Style.EMOJI['admin']}{Style.bold(' USER LIST ')}{Style.EMOJI['admin']}
╔══════════════════════════════════════╗
║         FIRST 10 USERS               ║
╚══════════════════════════════════════╝

"""
        for i, user in enumerate(users[:10], 1):
            status = "🚫 BANNED" if user['is_banned'] else "✅ ACTIVE"
            name = user['first_name'] or "Unknown"
            text += f"{i}. <code>{user['user_id']}</code> - {name}\n"
            text += f"   └ Credits: {user['credits']} | Searches: {user['total_searches']} | {status}\n\n"
        
        text += f"Total Users: {len(users)}\n"
        text += "Use /userinfo <user_id> for details"
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    @admin_only
    async def admin_user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get detailed user info"""
        try:
            user_id = int(context.args[0]) if context.args else None
            if not user_id:
                await update.message.reply_text(f"{Style.EMOJI['error']} Usage: /userinfo <user_id>")
                return
            
            user = await self.db.get_user(user_id)
            if not user:
                await update.message.reply_text(f"{Style.EMOJI['error']} User not found!")
                return
            
            # Get recent searches
            async with aiosqlite.connect(Config.DB_PATH) as db:
                cursor = await db.execute("""
                    SELECT mobile_number, search_time, status 
                    FROM search_history 
                    WHERE user_id = ? 
                    ORDER BY search_time DESC 
                    LIMIT 5
                """, (user_id,))
                searches = await cursor.fetchall()
            
            text = f"""
{Style.EMOJI['admin']}{Style.bold(' USER DETAILS ')}{Style.EMOJI['admin']}
╔══════════════════════════════════════╗
║         USER INFORMATION             ║
╚══════════════════════════════════════╝

👤 ID: <code>{user['user_id']}</code>
📝 Name: {user['first_name'] or 'N/A'} {user['last_name'] or ''}
📧 Username: @{user['username'] if user['username'] else 'N/A'}

💰 Credits: {user['credits']}
📊 Total Used: {user['total_credits_used']}
🔍 Searches: {user['total_searches']}

🚫 Banned: {'Yes' if user['is_banned'] else 'No'}
📅 Joined: {user['join_date']}
🕐 Last Active: {user['last_active']}

📋 Notes: {user['notes'] or 'None'}

{Style.bold('Recent Searches:')}
"""
            for search in searches[:5]:
                time_str = search[1][:19] if search[1] else 'Unknown'
                status_emoji = '✅' if search[2] == 'success' else '❌'
                text += f"{status_emoji} {search[0]} at {time_str}\n"
            
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            await update.message.reply_text(f"{Style.EMOJI['error']} Error: {e}")
    
    @admin_only
    async def admin_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View admin logs"""
        async with aiosqlite.connect(Config.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM admin_logs 
                ORDER BY timestamp DESC 
                LIMIT 20
            """)
            logs = await cursor.fetchall()
        
        text = f"""
{Style.EMOJI['admin']}{Style.bold(' ADMIN LOGS ')}{Style.EMOJI['admin']}
╔══════════════════════════════════════╗
║         RECENT ACTIVITY              ║
╚══════════════════════════════════════╝

"""
        for log in logs[:10]:
            time_str = log['timestamp'][:19] if log['timestamp'] else 'Unknown'
            text += f"🕐 {time_str}\n"
            text += f"👤 Admin: {log['admin_id']}\n"
            text += f"⚡ Action: {log['action']}\n"
            text += f"🎯 Target: {log['target_user'] or 'None'}\n"
            text += f"📝 Details: {log['details'] or 'None'}\n\n"
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    @admin_only
    async def admin_clear_cache(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear osint cache"""
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute("DELETE FROM vishal_cache")
            await db.commit()
        
        await update.message.reply_text(
            f"{Style.EMOJI['success']} osint cache cleared successfully!"
        )
    
    # ============================================
    # 🔄 CALLBACK HANDLERS
    # ============================================
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        # Get user data
        db_user = await self.db.get_user(user_id)
        
        if data == "back_main":
            await query.edit_message_text(
                f"{Style.EMOJI['heart']} Main Menu",
                reply_markup=self.ui.main_menu(db_user)
            )
        
        elif data == "search":
            await query.edit_message_text(
                f"{Style.EMOJI['search']} Send me a 10-digit mobile number to search!\n\n"
                f"Example: <code>9936265050</code>",
                parse_mode=ParseMode.HTML
            )
        
        elif data == "credits":
            daily_credits = await self.db.get_daily_credits(user_id)
            text = f"""
{Style.EMOJI['credit']}{Style.bold(' YOUR CREDITS ')}{Style.EMOJI['credit']}
╔══════════════════════════════════════╗
║         BALANCE DETAILS              ║
╚══════════════════════════════════════╝

💰 Balance: {Style.bold(db_user['credits'])} credits
🎁 Daily Used: {Style.bold(f'{daily_credits}/{Config.FREE_DAILY_CREDITS}')}
📊 Total Used: {Style.bold(db_user['total_credits_used'])} credits

/free - Get free credits
/buy - Purchase credits
/refer - Refer friends
"""
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="back_main")
                ]])
            )
        
        elif data == "history":
            async with aiosqlite.connect(Config.DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT mobile_number, search_time, status 
                    FROM search_history 
                    WHERE user_id = ? 
                    ORDER BY search_time DESC 
                    LIMIT 5
                """, (user_id,))
                rows = await cursor.fetchall()
            
            if not rows:
                text = f"{Style.EMOJI['info']} No search history yet."
            else:
                text = f"{Style.EMOJI['history']}{Style.bold(' RECENT SEARCHES ')}{Style.EMOJI['history']}\n\n"
                for row in rows:
                    time_str = datetime.fromisoformat(row['search_time']).strftime('%H:%M %d/%m')
                    status = "✅" if row['status'] == 'success' else "❌"
                    text += f"{status} <code>{row['mobile_number']}</code> at {time_str}\n"
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="back_main")
                ]])
            )
        
        elif data == "free":
            await self.free_credits(update, context)
        
        elif data == "buy":
            plans_text = f"{Style.EMOJI['money']}{Style.bold(' BUY CREDITS ')}{Style.EMOJI['money']}\n\n"
            for plan_id, plan in Config.PLANS.items():
                plans_text += f"{plan['emoji']} {plan['name']}: {plan['credits']} credits - ₹{plan['price']}\n"
            
            await query.edit_message_text(
                plans_text,
                parse_mode=ParseMode.HTML,
                reply_markup=self.ui.buy_credits_menu()
            )
        
        elif data == "stats":
            await self.stats_command(update, context)
        
        elif data == "help":
            await self.help_command(update, context)
        
        elif data == "refer":
            await self.refer_command(update, context)
        
        elif data == "admin":
            if user_id in Config.ADMIN_IDS:
                await self.admin_panel(update, context)
        
        elif data.startswith("buy_"):
            plan_id = data.replace("buy_", "")
            plan = Config.PLANS.get(plan_id)
            
            if plan:
                # Generate payment link/instructions
                payment_text = f"""
{Style.EMOJI['money']}{Style.bold(' PURCHASE PLAN ')}{Style.EMOJI['money']}
╔══════════════════════════════════════╗
║         PAYMENT DETAILS              ║
╚══════════════════════════════════════╝

Plan: {plan['emoji']} {plan['name']}
Credits: {plan['credits']}
Price: ₹{plan['price']}

{Style.bold('Payment Details:')}
UPI ID: <code>{Config.UPI_ID}</code>

{Style.bold('Instructions:')}
1️⃣ Pay ₹{plan['price']} to above UPI ID
2️⃣ Send screenshot with transaction ID
3️⃣ Wait for admin verification (5-10 min)

{Style.EMOJI['info']} Credits will be added automatically after verification
"""
                keyboard = [
                    [InlineKeyboardButton("✅ I've Paid", callback_data=f"verify_{plan_id}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="buy")]
                ]
                
                await query.edit_message_text(
                    payment_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        
        elif data.startswith("verify_"):
            plan_id = data.replace("verify_", "")
            plan = Config.PLANS.get(plan_id)
            
            # Store payment request
            async with aiosqlite.connect(Config.DB_PATH) as db:
                await db.execute("""
                    INSERT INTO transactions (user_id, amount, credits, transaction_type, status)
                    VALUES (?, ?, ?, 'purchase', 'pending')
                """, (user_id, plan['price'], plan['credits']))
                await db.commit()
            
            await query.edit_message_text(
                f"{Style.EMOJI['success']} Payment verification requested!\n\n"
                f"Your request has been sent to admins.\n"
                f"You will receive credits within 5-10 minutes.\n\n"
                f"Transaction ID: <code>TXN{user_id}{int(time.time())}</code>",
                parse_mode=ParseMode.HTML
            )
            
            # Notify admins
            for admin_id in Config.ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"{Style.EMOJI['money']} New payment request!\n\n"
                        f"👤 User: {user_id}\n"
                        f"💰 Plan: {plan['name']}\n"
                        f"💵 Amount: ₹{plan['price']}\n"
                        f"🎫 Credits: {plan['credits']}\n\n"
                        f"Use /addcredits {user_id} {plan['credits']} to approve"
                    )
                except:
                    pass
        
        # Admin callbacks
        elif data == "admin_dashboard" and user_id in Config.ADMIN_IDS:
            stats = await self.db.get_stats()
            text = f"""
{Style.EMOJI['stats']}{Style.bold(' ADMIN DASHBOARD ')}{Style.EMOJI['stats']}
╔══════════════════════════════════════╗
║         SYSTEM STATUS                ║
╚══════════════════════════════════════╝

👥 Users: {stats['total_users']}
📈 Active: {stats['active_users']}
🔍 Searches: {stats['total_searches']}
💰 Credits Used: {stats['total_credits']}
✅ Success: {stats['successful']}
❌ Failed: {stats['failed']}
💵 Earnings: ₹{stats['total_earnings']}

🤖 osint: {'✅' if VISHAI_AVAILABLE else '❌'}
"""
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=self.ui.admin_menu()
            )
        
        elif data == "admin_users" and user_id in Config.ADMIN_IDS:
            await self.admin_users_list(update, context)
        
        elif data == "admin_credits" and user_id in Config.ADMIN_IDS:
            text = f"""
{Style.EMOJI['admin']}{Style.bold(' CREDIT MANAGEMENT ')}{Style.EMOJI['admin']}

{Style.bold('Commands:')}
/addcredits <user_id> <amount> - Add credits
/removecredits <user_id> <amount> - Remove credits
/checkcredits <user_id> - Check user credits

{Style.bold('Pending Transactions:')}
"""
            # Get pending transactions
            async with aiosqlite.connect(Config.DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM transactions 
                    WHERE status = 'pending' 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                pending = await cursor.fetchall()
            
            if pending:
                for p in pending:
                    text += f"\n🆔 {p['user_id']} - ₹{p['amount']} for {p['credits']} credits"
            else:
                text += "\nNo pending transactions"
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin")
                ]])
            )
        
        elif data == "admin_broadcast" and user_id in Config.ADMIN_IDS:
            await self.admin_broadcast_start(update, context)
        
        elif data == "admin_ban" and user_id in Config.ADMIN_IDS:
            text = f"""
{Style.EMOJI['admin']}{Style.bold(' BAN MANAGEMENT ')}{Style.EMOJI['admin']}

{Style.bold('Commands:')}
/ban <user_id> <reason> - Ban a user
/unban <user_id> - Unban a user
/bannedlist - List banned users

{Style.bold('Recently Banned:')}
"""
            # Get banned users
            banned = await self.db.get_all_users(banned_only=True)
            if banned:
                for b in banned[:5]:
                    text += f"\n🚫 {b['user_id']} - {b['first_name'] or 'Unknown'}"
            else:
                text += "\nNo banned users"
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin")
                ]])
            )
        
        elif data == "admin_logs" and user_id in Config.ADMIN_IDS:
            await self.admin_logs(update, context)
        
        elif data == "admin_settings" and user_id in Config.ADMIN_IDS:
            text = f"""
{Style.EMOJI['admin']}{Style.bold(' ADMIN SETTINGS ')}{Style.EMOJI['admin']}

{Style.bold('Current Configuration:')}
🤖 osint: {'✅ Available' if VISHAI_AVAILABLE else '❌ Not Installed'}
💰 Default Credits: {Config.DEFAULT_CREDITS}
🎁 Daily Free: {Config.FREE_DAILY_CREDITS}
👥 Referral Bonus: {Config.REFERRAL_BONUS}
⚡ Rate Limit: {Config.RATE_LIMIT}/min
💾 Cache TTL: {Config.CACHE_TTL}s

{Style.bold('Actions:')}
/clearcache - Clear osint cache
/restart - Restart bot (if using systemd)
"""
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🗑️ Clear Cache", callback_data="admin_clearcache"),
                    InlineKeyboardButton("🔙 Back", callback_data="admin")
                ]])
            )
        
        elif data == "admin_clearcache" and user_id in Config.ADMIN_IDS:
            await self.admin_clear_cache(update, context)

# ============================================
# 🚀 MAIN FUNCTION
# ============================================
def main():
    """Main function to run the bot"""
    
    # Check if Osint is available
    if not VISHAI_AVAILABLE:
        print("""
╔══════════════════════════════════════════════════════════╗
║  ❌ osint not installed!                    ║
╠══════════════════════════════════════════════════════════╣
║  Please install it using:                                ║
║                                                          ║
║  pip install vishal-info v                               ║
║                                                          ║
║  Or from source:                                         ║
║  pip install git+https://github.com/vishal-info/        ║
║  vishal-info.git                                         ║
║                                                          ║
║  The bot will still work but without the main feature!   ║
╚══════════════════════════════════════════════════════════╝
        """)
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Check bot token
    if Config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("""
╔══════════════════════════════════════════════════════════╗
║  ❌ Bot token not configured!                            ║
╠══════════════════════════════════════════════════════════╣
║  Please set your bot token in:                           ║
║  1. Create .env file                                     ║
║  2. Add: BOT_TOKEN=your_token_here                       ║
║                                                          ║
║  Get token from @BotFather                               ║
╚══════════════════════════════════════════════════════════╝
        """)
        sys.exit(1)
    
    # Create bot instance
    bot = VishalInfoBot()
    
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("credits", bot.credits_command))
    application.add_handler(CommandHandler("free", bot.free_credits))
    application.add_handler(CommandHandler("buy", bot.buy_credits))
    application.add_handler(CommandHandler("history", bot.history_command))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("refer", bot.refer_command))
    
    # Admin command handlers
    application.add_handler(CommandHandler("admin", bot.admin_panel))
    application.add_handler(CommandHandler("addcredits", bot.admin_add_credits))
    application.add_handler(CommandHandler("removecredits", bot.admin_remove_credits))
    application.add_handler(CommandHandler("ban", bot.admin_ban_user))
    application.add_handler(CommandHandler("unban", bot.admin_unban_user))
    application.add_handler(CommandHandler("userinfo", bot.admin_user_info))
    application.add_handler(CommandHandler("clearcache", bot.admin_clear_cache))
    
    # Broadcast conversation handler
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", bot.admin_broadcast_start)],
        states={
            bot.WAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.admin_broadcast_message)]
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)]
    )
    application.add_handler(broadcast_conv)
    
    # Message handler for mobile numbers
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'^[\d\s\+\-\(\)]+$'), 
        bot.handle_number
    ))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(bot.callback_handler))
    
    # Start the bot
    print("""
╔══════════════════════════════════════════════════════════╗
║  🌟 VISHAI INFO BOT STARTED SUCCESSFULLY! 🌟            ║
╠══════════════════════════════════════════════════════════╣
║  🤖 Using osint: {}                         ║
║  👥 Admin IDs: {}                       ║
║  📱 Default credits: {}                                   ║
║  🎁 Daily free: {}                                        ║
║  💾 Database: {}                      ║
║                                                          ║
║  ⏰ Time: {}                         ║
║  📢 Join: {}                       ║
╚══════════════════════════════════════════════════════════╝
    """.format(
        "✅ Available" if VISHAI_AVAILABLE else "❌ Not Installed",
        len(Config.ADMIN_IDS),
        Config.DEFAULT_CREDITS,
        Config.FREE_DAILY_CREDITS,
        Config.DB_PATH,
        datetime.now(Config.TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'),
        Config.REQUIRED_CHANNEL
    ))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)