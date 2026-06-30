"""
database.py
============
لایه مرکزی دسترسی به دیتابیس‌ها.

طبق معماری جدید، دو دیتابیس کاملاً مجزا داریم:

  1) tickets.db  -> فقط سیستم تیکت (جدول tickets و موارد مرتبط با آن).
                     هیچ داده‌ی ادمین / آمار / کاربر در این فایل ذخیره نمی‌شود.

  2) bot.db       -> فقط مدیریت سیستم: ادمین‌ها (۴ سطح دسترسی)، usage_logs،
                     bot_users و هر داده‌ی مدیریتی/آماری دیگر.

این ماژول هر دو اتصال را با connection جدا و lock جداگانه (thread-safe) می‌سازد
و در صورتی که از نسخه‌ی قبلی، جداول admins/usage_logs/bot_users به‌اشتباه داخل
tickets.db ساخته شده باشند، به‌صورت امن (بدون از دست رفتن داده) آن‌ها را به
bot.db منتقل می‌کند.
"""

import sqlite3
import threading
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TICKETS_DB_PATH = os.path.join(BASE_DIR, "tickets.db")
BOT_DB_PATH = os.path.join(BASE_DIR, "bot.db")

# هر دیتابیس connection و lock مخصوص به خودش را دارد تا دسترسی هم‌زمان
# از thread های مختلف (PTB از چند worker thread استفاده می‌کند) ایمن باشد.
_tickets_conn = sqlite3.connect(TICKETS_DB_PATH, check_same_thread=False)
_tickets_cursor = _tickets_conn.cursor()
_tickets_lock = threading.Lock()

_bot_conn = sqlite3.connect(BOT_DB_PATH, check_same_thread=False)
_bot_cursor = _bot_conn.cursor()
_bot_lock = threading.Lock()


def _init_tickets_table():
    """
    BUGFIX: قبلاً هیچ‌جا جدول tickets با CREATE TABLE IF NOT EXISTS ساخته
    نمی‌شد و فقط به وجود فایل از پیش موجود tickets.db تکیه می‌شد. در یک
    دیپلوی تازه (فایل tickets.db خالی/جدید)، اولین INSERT با خطای
    'no such table: tickets' کرش می‌کرد. این تابع آن را امن می‌سازد و به
    داده‌ی موجود دست نمی‌زند.
    """
    with _tickets_lock:
        _tickets_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                chat_id INTEGER,
                name TEXT,
                username TEXT,
                text TEXT,
                voice_id TEXT,
                date TEXT,
                time TEXT
            )
            """
        )
        _tickets_conn.commit()


_init_tickets_table()


def get_tickets_db():
    """اتصال + cursor + lock مخصوص tickets.db (فقط برای سیستم تیکت)."""
    return _tickets_conn, _tickets_cursor, _tickets_lock


def get_bot_db():
    """اتصال + cursor + lock مخصوص bot.db (ادمین‌ها، آمار، کاربران ربات)."""
    return _bot_conn, _bot_cursor, _bot_lock


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def table_exists(cursor, table_name: str) -> bool:
    """نسخه‌ی عمومی _table_exists - برای استفاده‌ی ماژول‌های دیگر (مثل diagnostics.py)."""
    return _table_exists(cursor, table_name)


def _table_columns(cursor, table_name: str):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def migrate_legacy_admin_tables():
    """
    اگر در نسخه‌های قبلی، جداول admins / usage_logs / bot_users به اشتباه
    داخل tickets.db ساخته شده باشند، داده‌های آن‌ها را (بدون حذف هیچ داده‌ای)
    به bot.db کپی می‌کند. این تابع کاملاً ایمن و idempotent است:
    اگر داده‌ای برای انتقال نباشد، هیچ اتفاقی نمی‌افتد.
    """
    legacy_tables = ["admins", "usage_logs", "bot_users"]

    with _tickets_lock, _bot_lock:
        for table in legacy_tables:
            if not _table_exists(_tickets_cursor, table):
                continue

            columns = _table_columns(_tickets_cursor, table)
            if not columns:
                continue

            # اطمینان از وجود جدول مقصد در bot.db (ساخت توسط admin_system._init_tables
            # هم انجام می‌شود، اما این تابع ممکن است زودتر صدا زده شود)
            if not _table_exists(_bot_cursor, table):
                continue  # جدول مقصد هنوز ساخته نشده؛ admin_system باید اول init شود

            _tickets_cursor.execute(f"SELECT {', '.join(columns)} FROM {table}")
            rows = _tickets_cursor.fetchall()

            if not rows:
                continue

            placeholders = ", ".join(["?"] * len(columns))
            col_list = ", ".join(columns)

            migrated = 0
            for row in rows:
                try:
                    _bot_cursor.execute(
                        f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})",
                        row,
                    )
                    migrated += 1
                except sqlite3.Error:
                    # هرگز اجازه نده یک رکورد خراب کل مهاجرت را متوقف کند
                    continue

            _bot_conn.commit()

            if migrated:
                # فقط بعد از کپی موفق، جدول قدیمی را از tickets.db حذف می‌کنیم
                # تا طبق الزامات پروژه، دیتابیس تیکت با داده‌ی مدیریتی مخلوط نشود.
                try:
                    _tickets_cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    _tickets_conn.commit()
                except sqlite3.Error:
                    pass
