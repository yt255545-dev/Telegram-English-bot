"""
SQLite storage for questions, per-user answers, and monthly / all-time leaderboards.
"""
import sqlite3
import datetime
from contextlib import contextmanager
from config import DB_PATH


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        );

        CREATE TABLE IF NOT EXISTS quiz_sets (
            set_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER,
            chat_message_id INTEGER,
            question_text TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_option TEXT,
            FOREIGN KEY(set_id) REFERENCES quiz_sets(set_id)
        );

        CREATE TABLE IF NOT EXISTS answers (
            question_id INTEGER,
            user_id INTEGER,
            chosen_option TEXT,
            is_correct INTEGER,
            answered_at TEXT,
            PRIMARY KEY (question_id, user_id)
        );
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_user(user_id, username, first_name):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name",
            (user_id, username, first_name),
        )


def create_quiz_set(topic):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO quiz_sets (topic, created_at) VALUES (?, ?)",
            (topic, datetime.datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def add_question(set_id, question_text, options, correct_option, chat_message_id=None):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO questions
               (set_id, chat_message_id, question_text, option_a, option_b, option_c, option_d, correct_option)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (set_id, chat_message_id, question_text, options[0], options[1], options[2], options[3], correct_option),
        )
        return cur.lastrowid


def set_question_message_id(question_id, chat_message_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE questions SET chat_message_id=? WHERE question_id=?",
            (chat_message_id, question_id),
        )


def get_question(question_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM questions WHERE question_id=?", (question_id,)).fetchone()
        return dict(row) if row else None


def has_answered(question_id, user_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM answers WHERE question_id=? AND user_id=?", (question_id, user_id)
        ).fetchone()
        return row is not None


def record_answer(question_id, user_id, chosen_option, is_correct):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO answers (question_id, user_id, chosen_option, is_correct, answered_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (question_id, user_id, chosen_option, int(is_correct), datetime.datetime.utcnow().isoformat()),
        )


def count_answers(question_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) c FROM answers WHERE question_id=?", (question_id,)
        ).fetchone()
        return row["c"]


def top_monthly(year_month, limit=10):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT u.user_id, u.username, u.first_name, SUM(a.is_correct) AS score
            FROM answers a
            JOIN users u ON u.user_id = a.user_id
            WHERE substr(a.answered_at, 1, 7) = ?
            GROUP BY u.user_id
            ORDER BY score DESC
            LIMIT ?
            """,
            (year_month, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def top_alltime(limit=10):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT u.user_id, u.username, u.first_name, SUM(a.is_correct) AS score
            FROM answers a
            JOIN users u ON u.user_id = a.user_id
            GROUP BY u.user_id
            ORDER BY score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
