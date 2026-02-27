"""
database.py — SQLite integration for CurricuForge.
Stores generated curricula, semesters, and courses locally.
No external database server required.
"""

import os
import json
import hashlib
import secrets
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional

# Database file — stored in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curricuforge.db")


async def init_db():
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS curricula (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      TEXT DEFAULT (datetime('now')),
                skill           TEXT NOT NULL,
                level           TEXT NOT NULL,
                num_semesters   INTEGER NOT NULL,
                weekly_hours    INTEGER NOT NULL,
                industry        TEXT,
                goals           TEXT,
                style           TEXT,
                selected_topics TEXT,
                notes           TEXT,
                summary         TEXT,
                agent_plan      TEXT,
                agent_review    TEXT,
                raw_output      TEXT
            );

            CREATE TABLE IF NOT EXISTS semesters (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                curriculum_id   INTEGER NOT NULL,
                semester_number INTEGER NOT NULL,
                title           TEXT NOT NULL,
                FOREIGN KEY (curriculum_id) REFERENCES curricula(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS courses (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                semester_id     INTEGER NOT NULL,
                course_name     TEXT NOT NULL,
                credits         INTEGER DEFAULT 3,
                duration_weeks  INTEGER DEFAULT 15,
                description     TEXT,
                topics          TEXT,
                FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at      TEXT DEFAULT (datetime('now')),
                full_name       TEXT NOT NULL,
                email           TEXT UNIQUE NOT NULL,
                password_hash   TEXT NOT NULL,
                salt            TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                token           TEXT UNIQUE NOT NULL,
                created_at      TEXT DEFAULT (datetime('now')),
                expires_at      TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        await db.commit()
        print(f"[DB] SQLite database initialized at: {DB_PATH}")


async def save_curriculum(input_data: dict, parsed: dict, plan: str, review: str, raw_output: str) -> Optional[int]:
    """
    Save a generated curriculum to SQLite.
    Returns the curriculum ID.
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Enable foreign keys
            await db.execute("PRAGMA foreign_keys = ON")

            # Insert main curriculum record
            cursor = await db.execute("""
                INSERT INTO curricula (skill, level, num_semesters, weekly_hours,
                                      industry, goals, style, selected_topics, notes,
                                      summary, agent_plan, agent_review, raw_output)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                input_data.get('skill', ''),
                input_data.get('level', 'undergraduate'),
                input_data.get('semesters', 4),
                input_data.get('hours', 15),
                input_data.get('industry', ''),
                input_data.get('goals', ''),
                input_data.get('style', 'balanced'),
                json.dumps(input_data.get('selectedTopics', [])),
                input_data.get('notes', ''),
                parsed.get('summary', ''),
                plan or '',
                review or '',
                raw_output or ''
            ))
            curriculum_id = cursor.lastrowid

            # Insert semesters and courses
            for sem in parsed.get('semesters', []):
                sem_cursor = await db.execute("""
                    INSERT INTO semesters (curriculum_id, semester_number, title)
                    VALUES (?, ?, ?)
                """, (curriculum_id, sem['number'], sem['title']))
                semester_id = sem_cursor.lastrowid

                for course in sem.get('courses', []):
                    await db.execute("""
                        INSERT INTO courses (semester_id, course_name, credits, duration_weeks, description, topics)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        semester_id,
                        course.get('name', 'Untitled Course'),
                        course.get('credits', 3),
                        course.get('duration', 15),
                        course.get('description', ''),
                        json.dumps(course.get('topics', []))
                    ))

            await db.commit()
            print(f"[DB] Curriculum saved with ID: {curriculum_id}")
            return curriculum_id

    except Exception as e:
        print(f"[DB] Error saving curriculum: {e}")
        return None


async def get_curriculum(curriculum_id: int) -> Optional[dict]:
    """Retrieve a stored curriculum by ID."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute("SELECT * FROM curricula WHERE id = ?", (curriculum_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                result = dict(row)
                result['selected_topics'] = json.loads(result.get('selected_topics', '[]'))

            # Fetch semesters
            result['semesters'] = []
            async with db.execute(
                "SELECT * FROM semesters WHERE curriculum_id = ? ORDER BY semester_number",
                (curriculum_id,)
            ) as cursor:
                semesters = await cursor.fetchall()

            for sem in semesters:
                sem_dict = dict(sem)

                # Fetch courses for this semester
                async with db.execute(
                    "SELECT * FROM courses WHERE semester_id = ?", (sem_dict['id'],)
                ) as cursor:
                    courses = await cursor.fetchall()

                sem_dict['courses'] = []
                for c in courses:
                    course_dict = dict(c)
                    course_dict['topics'] = json.loads(course_dict.get('topics', '[]'))
                    sem_dict['courses'].append(course_dict)

                result['semesters'].append(sem_dict)

            return result

    except Exception as e:
        print(f"[DB] Error retrieving curriculum: {e}")
        return None


async def list_curricula(limit: int = 20) -> list:
    """List recent curricula."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, skill, level, num_semesters, created_at FROM curricula ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB] Error listing curricula: {e}")
        return []


async def close_pool():
    """No-op for SQLite (no connection pool to close)."""
    print("[DB] SQLite connection closed.")


# ══════════════════════════════════════════════════════════════════════
#  AUTH FUNCTIONS
# ══════════════════════════════════════════════════════════════════════
def hash_password(password: str, salt: str = None) -> tuple:
    """Hash a password with a salt. Returns (hash, salt)."""
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pw_hash, salt


async def create_user(full_name: str, email: str, password: str) -> Optional[int]:
    """Create a new user. Returns user ID or None if email exists."""
    try:
        pw_hash, salt = hash_password(password)
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "INSERT INTO users (full_name, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (full_name, email.lower().strip(), pw_hash, salt)
            )
            await db.commit()
            user_id = cursor.lastrowid
            print(f"[DB] User created: {email} (ID: {user_id})")
            return user_id
    except aiosqlite.IntegrityError:
        print(f"[DB] User already exists: {email}")
        return None
    except Exception as e:
        print(f"[DB] Error creating user: {e}")
        return None


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Verify email/password. Returns user dict or None."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                user = dict(row)

            # Verify password
            pw_hash, _ = hash_password(password, user['salt'])
            if pw_hash != user['password_hash']:
                return None

            return {
                'id': user['id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'created_at': user['created_at']
            }
    except Exception as e:
        print(f"[DB] Auth error: {e}")
        return None


async def create_session(user_id: int) -> Optional[str]:
    """Create a session token for a user. Returns token string."""
    try:
        token = secrets.token_urlsafe(32)
        expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expires)
            )
            await db.commit()
        return token
    except Exception as e:
        print(f"[DB] Session create error: {e}")
        return None


async def get_user_by_token(token: str) -> Optional[dict]:
    """Look up user by session token. Returns user dict or None."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT u.id, u.full_name, u.email, u.created_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND s.expires_at > datetime('now')
            """, (token,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    except Exception as e:
        print(f"[DB] Token lookup error: {e}")
        return None


async def delete_session(token: str):
    """Delete a session token (logout)."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            await db.commit()
    except Exception as e:
        print(f"[DB] Session delete error: {e}")
