"""
Database setup and operations using SQLite
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .logger import logger


DB_PATH = os.getenv("DB_PATH", "/app/data/alarms.db")


def init_db():
    """Initialize database with required tables"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Alarms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('one-time', 'recurring')),
            time TEXT NOT NULL,
            date TEXT,
            days TEXT,
            timezone TEXT DEFAULT 'UTC',
            created_at TEXT NOT NULL
        )
    """)
    
    # Videos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            added_at TEXT NOT NULL
        )
    """)
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Alarm operations
def create_alarm(alarm_type: str, time: str, date: Optional[str] = None, 
                 days: Optional[str] = None, timezone: str = "UTC") -> int:
    """Create a new alarm"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO alarms (type, time, date, days, timezone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (alarm_type, time, date, days, timezone, datetime.utcnow().isoformat())
        )
        conn.commit()
        alarm_id = cursor.lastrowid
        logger.info(f"Created {alarm_type} alarm with ID {alarm_id}")
        return alarm_id


def get_all_alarms() -> List[Dict[str, Any]]:
    """Get all alarms"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alarms ORDER BY id")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_alarm(alarm_id: int) -> bool:
    """Delete an alarm by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted alarm ID {alarm_id}")
        return deleted


# Video operations
def add_video(url: str) -> Optional[int]:
    """Add a video URL"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO videos (url, added_at) VALUES (?, ?)",
                (url, datetime.utcnow().isoformat())
            )
            conn.commit()
            video_id = cursor.lastrowid
            logger.info(f"Added video ID {video_id}")
            return video_id
        except sqlite3.IntegrityError:
            logger.warning(f"Video already exists: {url}")
            return None


def get_all_videos() -> List[Dict[str, Any]]:
    """Get all videos"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY id")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_video(video_id: Optional[int] = None, url: Optional[str] = None) -> bool:
    """Delete a video by ID or URL"""
    with get_db() as conn:
        cursor = conn.cursor()
        if video_id:
            cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        elif url:
            cursor.execute("DELETE FROM videos WHERE url = ?", (url,))
        else:
            return False
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted video (ID: {video_id}, URL: {url})")
        return deleted


# Settings operations
def set_setting(key: str, value: str) -> None:
    """Set a setting value"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=?, updated_at=?
            """,
            (key, value, datetime.utcnow().isoformat(), value, datetime.utcnow().isoformat())
        )
        conn.commit()
        logger.info(f"Set setting {key}={value}")


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a setting value"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default
