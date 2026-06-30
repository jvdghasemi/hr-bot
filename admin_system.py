"""
admin_system.py
================
ماژول مستقل برای:
  1) آمار ماهانه/روزانه استفاده از ربات (Usage Statistics)
  2) سیستم مدیریت ادمین‌ها با ۴ سطح دسترسی (Permission Levels)

این نسخه به جای دیتابیس جداگانه، از همان اتصال دیتابیس اصلی ربات (tickets.db)
استفاده می‌کند تا همه چیز در یک فایل دیتابیس واحد بماند.
رابط کاربری کاملاً با دکمه‌های شیشه‌ای (InlineKeyboard) است؛ هیچ دستور متنی
مثل /addadmin لازم نیست — منطق آن در bot.py با callback_data پیاده شده.

سطوح دسترسی (هرچه عدد کمتر، دسترسی بیشتر):
    1 = Super Owner / Owner   (دسترسی کامل - تغییر سطح ادمین‌ها - افزودن/حذف ادمین - انتقال مالکیت)
    2 = Senior Admin          (مدیریت تیکت‌ها - پیام همگانی - مشاهده آمار)
    3 = Moderator             (پاسخ به تیکت‌ها - مدیریت FAQ)
    4 = Support Staff         (دسترسی محدود به ابزارهای واگذار شده)

NEW (نسخه ۲): این ماژول دیگر دیتابیس را خودش باز نمی‌کند. اتصال از طریق
database.get_bot_db() گرفته می‌شود تا تمام داده‌های مدیریتی/آماری در
bot.db نگهداری شوند و هرگز با tickets.db (که فقط مخصوص تیکت‌هاست) قاطی نشوند.
"""

import os
import jdatetime
import pytz
from datetime import datetime

import database

# ================== تنظیمات سطح دسترسی ==================

LEVEL_SUPER_OWNER = 1
LEVEL_SENIOR_ADMIN = 2
LEVEL_MODERATOR = 3
LEVEL_SUPPORT_STAFF = 4

LEVEL_NAMES = {
    LEVEL_SUPER_OWNER: "👑 Super Owner",
    LEVEL_SENIOR_ADMIN: "🥈 Senior Admin",
    LEVEL_MODERATOR: "🥉 Moderator",
    LEVEL_SUPPORT_STAFF: "🔹 Support Staff",
}

LEVEL_PERMISSIONS = {
    LEVEL_SUPER_OWNER: {
        "manage_admins", "view_stats", "broadcast",
        "manage_tickets", "manage_faq", "full_access",
    },
    LEVEL_SENIOR_ADMIN: {
        "view_stats", "broadcast", "manage_tickets",
    },
    LEVEL_MODERATOR: {
        "manage_tickets", "manage_faq",
    },
    LEVEL_SUPPORT_STAFF: {
        "manage_tickets",
    },
}

# ================== Owner ID (تنظیم اولیه) ==================
OWNER_ID = 7186618503  # آیدی خودت
OWNER_ID_ENV = os.getenv("OWNER_ID")
OWNER_ID = int(OWNER_ID_ENV) if OWNER_ID_ENV else None

# ================== اتصال دیتابیس مشترک ==================
# NEW (v2): این ماژول از دیتابیس مستقل bot.db استفاده می‌کند (نه tickets.db)
# تا داده‌های ادمین/آمار هرگز با داده‌های تیکت مخلوط نشوند.
# اتصال به‌صورت خودکار از database.py گرفته می‌شود؛ نیازی به فراخوانی دستی
# نیست، اما bind_connection() برای سازگاری با نسخه‌های قبلی نگه داشته شده است.

_conn, _cursor, _db_lock = database.get_bot_db()


def bind_connection(conn=None, cursor=None, lock=None):
    """
    DEPRECATED (نگه‌داشته‌شده برای سازگاری عقب‌رو): دیگر لازم نیست از bot.py
    صدا زده شود؛ admin_system به‌صورت خودکار به bot.db متصل می‌شود.
    آرگومان‌ها نادیده گرفته می‌شوند؛ فقط جداول bot.db مطمئن می‌شوند ساخته شده‌اند
    و در صورت وجود جداول قدیمی داخل tickets.db، داده‌هایشان منتقل می‌شود.
    """
    _init_tables()
    try:
        database.migrate_legacy_admin_tables()
    except Exception:
        pass


def _init_tables():
    """
    ساخت جداول مورد نیاز داخل همان دیتابیس اصلی، در صورت عدم وجود.
    این تابع امن است و دیتای موجود (تیکت‌ها و ...) را دست نمی‌زند.
    """
    _cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            level INTEGER NOT NULL,
            full_name TEXT,
            added_by INTEGER,
            added_at TEXT
        )
    """)

    _cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            date TEXT NOT NULL,
            month TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    _cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_users (
            user_id INTEGER PRIMARY KEY,
            first_seen TEXT,
            last_seen TEXT
        )
    """)
    _cursor.execute(
        "INSERT OR IGNORE INTO admins (user_id, level) VALUES (?, ?)",
        (7186618503, 3)
    )

    _conn.commit()


# اطمینان از وجود جداول در همان لحظه import شدن ماژول
_init_tables()
try:
    database.migrate_legacy_admin_tables()
except Exception:
    pass


def _now_tehran():
    tehran = pytz.timezone("Asia/Tehran")
    return datetime.now(tehran)


def _shamsi_date_and_month(now=None):
    if now is None:
        now = _now_tehran()
    j = jdatetime.datetime.fromgregorian(datetime=now)
    return j.strftime("%Y/%m/%d"), j.strftime("%Y/%m")


# ================== ثبت آمار (Usage Tracking) ==================

def log_usage(user_id: int, action: str):
    """ثبت یک رویداد استفاده از ربات (start یا باز شدن یک بخش)."""
    now = _now_tehran()
    date_str, month_str = _shamsi_date_and_month(now)
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    with _db_lock:
        _cursor.execute(
            "INSERT INTO usage_logs (user_id, action, date, month, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, date_str, month_str, timestamp),
        )

        _cursor.execute(
            "SELECT user_id FROM bot_users WHERE user_id=?", (user_id,))
        exists = _cursor.fetchone()

        if exists is None:
            _cursor.execute(
                "INSERT INTO bot_users (user_id, first_seen, last_seen) VALUES (?, ?, ?)",
                (user_id, timestamp, timestamp),
            )
        else:
            _cursor.execute(
                "UPDATE bot_users SET last_seen=? WHERE user_id=?",
                (timestamp, user_id),
            )

        _conn.commit()


def get_monthly_stats(month: str = None) -> dict:
    if month is None:
        _, month = _shamsi_date_and_month()

    _cursor.execute(
        "SELECT COUNT(*) FROM usage_logs WHERE action='start' AND month=?", (month,)
    )
    total_starts = _cursor.fetchone()[0]

    _cursor.execute(
        "SELECT COUNT(DISTINCT user_id) FROM usage_logs WHERE month=?", (month,)
    )
    unique_users = _cursor.fetchone()[0]

    _cursor.execute(
        """
        SELECT action, COUNT(*) as cnt
        FROM usage_logs
        WHERE month=? AND action != 'start'
        GROUP BY action
        ORDER BY cnt DESC
        """,
        (month,),
    )
    sections = _cursor.fetchall()

    return {
        "month": month,
        "total_starts": total_starts,
        "unique_users": unique_users,
        "sections": sections,
    }


def get_daily_stats(date: str = None) -> dict:
    if date is None:
        date, _ = _shamsi_date_and_month()

    _cursor.execute(
        "SELECT COUNT(*) FROM usage_logs WHERE action='start' AND date=?", (date,)
    )
    total_starts = _cursor.fetchone()[0]

    _cursor.execute(
        "SELECT COUNT(DISTINCT user_id) FROM usage_logs WHERE date=?", (date,)
    )
    unique_users = _cursor.fetchone()[0]

    _cursor.execute(
        """
        SELECT action, COUNT(*) as cnt
        FROM usage_logs
        WHERE date=? AND action != 'start'
        GROUP BY action
        ORDER BY cnt DESC
        """,
        (date,),
    )
    sections = _cursor.fetchall()

    return {
        "date": date,
        "total_starts": total_starts,
        "unique_users": unique_users,
        "sections": sections,
    }


def get_total_users() -> int:
    _cursor.execute("SELECT COUNT(*) FROM bot_users")
    return _cursor.fetchone()[0]


def format_stats_message(stats: dict, label: str) -> str:
    lines = [
        f"📊 آمار {label}",
        "",
        f"🚀 تعداد کل /start: {stats['total_starts']:,}",
        f"👥 کاربران یکتا: {stats['unique_users']:,}",
        "",
        "📂 بازدید بخش‌ها:",
    ]

    if stats["sections"]:
        for action, count in stats["sections"]:
            lines.append(f"  • {action}: {count:,}")
    else:
        lines.append("  (هنوز داده‌ای ثبت نشده)")

    return "\n".join(lines)


# ================== سیستم سطح دسترسی ادمین‌ها ==================

def get_admin_level(user_id: int) -> int | None:
    """سطح دسترسی کاربر. Owner همیشه سطح ۱. اگر ادمین نباشد None."""
    if OWNER_ID is not None and user_id == OWNER_ID:
        return LEVEL_SUPER_OWNER

    _cursor.execute("SELECT level FROM admins WHERE user_id=?", (user_id,))
    row = _cursor.fetchone()
    return row[0] if row else None


def is_admin(user_id: int) -> bool:
    return get_admin_level(user_id) is not None


def has_permission(user_id: int, permission: str) -> bool:
    level = get_admin_level(user_id)
    if level is None:
        return False
    if level == LEVEL_SUPER_OWNER:
        return True
    return permission in LEVEL_PERMISSIONS.get(level, set())


def can_manage_admins(user_id: int) -> bool:
    """آیا این کاربر اجازه باز کردن پنل مدیریت ادمین‌ها (افزودن/حذف/تغییر سطح) را دارد؟"""
    level = get_admin_level(user_id)
    if level is None:
        return False
    if level == LEVEL_SUPER_OWNER:
        return True
    return "manage_admins" in LEVEL_PERMISSIONS.get(level, set())


def set_admin_level(target_id: int, level: int, actor_id: int, full_name: str = "") -> tuple[bool, str]:
    """
    تنظیم سطح دسترسی یک کاربر (افزودن ادمین جدید یا ارتقا/تنزل ادمین موجود).
    قوانین سلسله‌مراتبی:
      - actor باید مجوز manage_admins داشته باشد.
      - actor نمی‌تواند سطحی بالاتر یا برابر خودش به کسی بدهد (مگر خودش Owner باشد).
      - actor نمی‌تواند روی ادمینی که از خودش سطح بالاتر دارد تغییر اعمال کند.
      - Owner قابل تغییر توسط غیر-Owner نیست.
    """
    actor_level = get_admin_level(actor_id)

    if actor_level is None or not can_manage_admins(actor_id):
        return False, "❌ شما مجوز مدیریت ادمین‌ها را ندارید."

    if target_id == OWNER_ID and actor_id != OWNER_ID:
        return False, "❌ امکان تغییر سطح Super Owner وجود ندارد."

    if actor_level != LEVEL_SUPER_OWNER and level <= actor_level:
        return False, "❌ شما نمی‌توانید سطحی برابر یا بالاتر از خودتان اعطا کنید."

    existing_level = get_admin_level(target_id)
    if existing_level is not None and actor_level != LEVEL_SUPER_OWNER and existing_level < actor_level:
        return False, "❌ شما نمی‌توانید سطح این ادمین را تغییر دهید (سطح بالاتر دارد)."

    now = _now_tehran().strftime("%Y-%m-%d %H:%M:%S")

    with _db_lock:
        if existing_level is not None:
            _cursor.execute(
                "UPDATE admins SET level=? WHERE user_id=?", (level, target_id)
            )
        else:
            _cursor.execute(
                "INSERT INTO admins (user_id, level, full_name, added_by, added_at) VALUES (?, ?, ?, ?, ?)",
                (target_id, level, full_name, actor_id, now),
            )
        _conn.commit()

    return True, f"✅ سطح کاربر {target_id} روی «{LEVEL_NAMES[level]}» تنظیم شد."


def remove_admin(target_id: int, actor_id: int) -> tuple[bool, str]:
    actor_level = get_admin_level(actor_id)

    if actor_level is None or not can_manage_admins(actor_id):
        return False, "❌ شما مجوز مدیریت ادمین‌ها را ندارید."

    if target_id == OWNER_ID:
        return False, "❌ امکان حذف Super Owner وجود ندارد."

    target_level = get_admin_level(target_id)
    if target_level is None:
        return False, "❌ این کاربر ادمین نیست."

    if actor_level != LEVEL_SUPER_OWNER and target_level < actor_level:
        return False, "❌ شما نمی‌توانید ادمینی با سطح بالاتر از خودتان را حذف کنید."

    with _db_lock:
        _cursor.execute("DELETE FROM admins WHERE user_id=?", (target_id,))
        _conn.commit()

    return True, f"✅ ادمین {target_id} حذف شد."


def list_admins() -> list[tuple]:
    """لیست همه ادمین‌ها: [(user_id, level, full_name), ...] — به‌علاوه Owner از env (اگر در جدول نباشد)."""
    with _db_lock:
        _cursor.execute(
            "SELECT user_id, level, full_name FROM admins ORDER BY level ASC, user_id ASC")
        rows = list(_cursor.fetchall())

    if OWNER_ID is not None and not any(r[0] == OWNER_ID for r in rows):
        rows.insert(0, (OWNER_ID, LEVEL_SUPER_OWNER, "Owner (env)"))

    return rows


def get_admin_display_name(user_id: int, full_name: str = "") -> str:
    if full_name:
        return f"{full_name} ({user_id})"
    return str(user_id)


def get_permissions_text(level: int) -> str:
    """متن خوانا از مجوزهای یک سطح دسترسی - برای نمایش در جزئیات ادمین."""
    if level == LEVEL_SUPER_OWNER:
        return "همه‌ی دسترسی‌ها (Full Access)"
    perms = LEVEL_PERMISSIONS.get(level, set())
    if not perms:
        return "—"
    return "، ".join(sorted(perms))


# ================== NEW: انتقال مالکیت (Transfer Ownership) ==================

def transfer_ownership(new_owner_id: int, actor_id: int) -> tuple[bool, str]:
    """
    فقط Owner فعلی می‌تواند مالکیت را به ادمین دیگری منتقل کند.
    مالک قبلی به‌صورت خودکار به سطح Senior Admin تنزل پیدا می‌کند تا دسترسی
    کامل به سیستم را روی خودش نگه ندارد و سیستم تک-Owner باقی بماند.
    توجه: OWNER_ID از متغیر محیطی خوانده می‌شود، بنابراین این تابع تغییر را
    در جدول admins ثبت می‌کند؛ برای کامل شدن انتقال در همه‌ی ری‌استارت‌ها،
    متغیر محیطی OWNER_ID باید توسط مسئول دیپلوی به‌روزرسانی شود (در پیام به
    actor توضیح داده می‌شود).
    """
    global OWNER_ID

    if actor_id != OWNER_ID:
        return False, "❌ فقط مالک فعلی (Owner) می‌تواند مالکیت را منتقل کند."

    if new_owner_id == OWNER_ID:
        return False, "❌ این کاربر همین حالا هم Owner است."

    now = _now_tehran().strftime("%Y-%m-%d %H:%M:%S")
    old_owner_id = OWNER_ID

    with _db_lock:
        # ادمین جدید را به‌عنوان Super Owner ثبت/به‌روزرسانی کن
        _cursor.execute(
            "SELECT user_id FROM admins WHERE user_id=?", (new_owner_id,))
        if _cursor.fetchone() is None:
            _cursor.execute(
                "INSERT INTO admins (user_id, level, full_name, added_by, added_at) VALUES (?, ?, ?, ?, ?)",
                (new_owner_id, LEVEL_SUPER_OWNER, "", actor_id, now),
            )
        else:
            _cursor.execute(
                "UPDATE admins SET level=? WHERE user_id=?", (
                    LEVEL_SUPER_OWNER, new_owner_id)
            )

        # مالک قبلی به Senior Admin تنزل پیدا می‌کند (نه حذف کامل دسترسی)
        _cursor.execute(
            "SELECT user_id FROM admins WHERE user_id=?", (old_owner_id,))
        if _cursor.fetchone() is None:
            _cursor.execute(
                "INSERT INTO admins (user_id, level, full_name, added_by, added_at) VALUES (?, ?, ?, ?, ?)",
                (old_owner_id, LEVEL_SENIOR_ADMIN, "", actor_id, now),
            )
        else:
            _cursor.execute(
                "UPDATE admins SET level=? WHERE user_id=?", (
                    LEVEL_SENIOR_ADMIN, old_owner_id)
            )

        _conn.commit()

    # به‌روزرسانی درون‌حافظه‌ای برای همین اجرای ربات (تا ری‌استارت بعدی که OWNER_ID
    # باید از طریق متغیر محیطی هم تغییر کند تا دائمی بماند)
    OWNER_ID = new_owner_id

    return True, (
        f"✅ مالکیت با موفقیت به کاربر {new_owner_id} منتقل شد.\n"
        f"⚠️ توجه: برای دائمی شدن این تغییر پس از ری‌استارت ربات، متغیر محیطی "
        f"OWNER_ID باید روی {new_owner_id} تنظیم شود."
    )


# ================== NEW: آمار کلی/Lifetime + داشبورد آمار ==================

def get_lifetime_stats() -> dict:
    """آمار کل (از ابتدای راه‌اندازی ربات تا کنون) — مستقیماً از usage_logs محاسبه می‌شود."""
    _cursor.execute("SELECT COUNT(*) FROM usage_logs WHERE action='start'")
    total_starts = _cursor.fetchone()[0]

    _cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_logs")
    unique_users = _cursor.fetchone()[0]

    _cursor.execute("SELECT COUNT(*) FROM usage_logs")
    total_events = _cursor.fetchone()[0]

    return {
        "total_starts": total_starts,
        "unique_users": unique_users,
        "total_events": total_events,
    }


def get_most_used_sections(limit: int = 10) -> list[tuple]:
    """پربازدیدترین بخش‌های ربات در کل تاریخچه (به‌جز رویداد start)."""
    _cursor.execute(
        """
        SELECT action, COUNT(*) as cnt
        FROM usage_logs
        WHERE action != 'start'
        GROUP BY action
        ORDER BY cnt DESC
        LIMIT ?
        """,
        (limit,),
    )
    return _cursor.fetchall()


def build_dashboard_text() -> str:
    """
    متن کامل «📊 Bot Usage Dashboard» مطابق درخواست:
    Total Starts, Unique Users, Monthly Usage, Daily Usage, Most used sections.
    این تابع فقط باید برای ادمین‌ها (view_stats) نمایش داده شود.
    """
    lifetime = get_lifetime_stats()
    monthly = get_monthly_stats()
    daily = get_daily_stats()
    total_users = get_total_users()
    top_sections = get_most_used_sections(10)

    lines = [
        "📊 Bot Usage Dashboard",
        "",
        f"🚀 Total Starts (Lifetime): {lifetime['total_starts']:,}",
        f"👥 Unique Users (Lifetime): {lifetime['unique_users']:,}",
        f"👤 Total Registered Users: {total_users:,}",
        "",
        f"📆 Monthly Usage ({monthly['month']}):",
        f"   • Starts: {monthly['total_starts']:,}",
        f"   • Unique Users: {monthly['unique_users']:,}",
        "",
        f"📅 Daily Usage ({daily['date']}):",
        f"   • Starts: {daily['total_starts']:,}",
        f"   • Unique Users: {daily['unique_users']:,}",
        "",
        "📂 Most Used Sections (Lifetime):",
    ]

    if top_sections:
        for action, count in top_sections:
            lines.append(f"   • {action}: {count:,}")
    else:
        lines.append("   (هنوز داده‌ای ثبت نشده)")

    return "\n".join(lines)
