"""
diagnostics.py
===============
سیستم خود-تشخیصی (Self-Diagnostic) ربات.

⚠️ این ماژول فقط on-demand اجرا می‌شود (با زدن دکمه‌ی «🩺 تشخیص سیستم» در
پنل مدیریت، فقط برای ادمین‌هایی که مجوز view_stats یا manage_admins دارند).
هیچ تابعی از این ماژول به‌صورت خودکار/پس‌زمینه اجرا نمی‌شود و هیچ تاثیری
روی سرعت اجرای عادی ربات ندارد.

خروجی run_system_diagnostics() یک رشته‌ی چندخطی با همان فرمت درخواستی است:
    [OK] ...
    [WARNING] ...
    [ERROR] ...
"""

import sqlite3

import database
import admin_system


def _ok(lines, msg):
    lines.append(f"[OK] {msg}")


def _warn(lines, msg):
    lines.append(f"[WARNING] {msg}")


def _err(lines, msg):
    lines.append(f"[ERROR] {msg}")


def _check_database_health(lines):
    """اتصال به هر دو دیتابیس + وجود جداول ضروری."""
    try:
        bot_conn, bot_cursor, _ = database.get_bot_db()
        bot_cursor.execute("SELECT 1")
        _ok(lines, "Database connection (bot.db)")
    except Exception as e:
        _err(lines, f"bot.db connection failed: {e}")
        bot_cursor = None

    try:
        tickets_conn, tickets_cursor, _ = database.get_tickets_db()
        tickets_cursor.execute("SELECT 1")
        _ok(lines, "Database connection (tickets.db)")
    except Exception as e:
        _err(lines, f"tickets.db connection failed: {e}")
        tickets_cursor = None

    required_bot_tables = ["admins", "usage_logs", "bot_users"]
    if bot_cursor is not None:
        for table in required_bot_tables:
            try:
                if database.table_exists(bot_cursor, table):
                    _ok(lines, f"Table '{table}' exists (bot.db)")
                else:
                    _err(lines, f"Missing required table '{table}' in bot.db")
            except Exception as e:
                _err(lines, f"Could not verify table '{table}': {e}")

    if tickets_cursor is not None:
        try:
            if database.table_exists(tickets_cursor, "tickets"):
                _ok(lines, "Ticket system healthy (table 'tickets' exists)")
            else:
                _err(lines, "Missing required table 'tickets' in tickets.db")
        except Exception as e:
            _err(lines, f"Could not verify 'tickets' table: {e}")

        # اطمینان از اینکه داده‌ی ادمین/آمار به اشتباه داخل tickets.db نیست
        leaked = [
            t for t in required_bot_tables
            if database.table_exists(tickets_cursor, t)
        ]
        if leaked:
            _warn(
                lines,
                f"Admin/stat tables found inside tickets.db (should be in bot.db): {leaked}",
            )
        else:
            _ok(lines, "tickets.db is clean (no admin/stat tables mixed in)")


def _check_admin_system_health(lines):
    """حداقل یک Owner، اعتبار سطوح دسترسی، بارگذاری صحیح سیستم مجوزها."""
    try:
        admins = admin_system.list_admins()
    except Exception as e:
        _err(lines, f"Could not load admin list: {e}")
        return

    owners = [a for a in admins if a[1] == admin_system.LEVEL_SUPER_OWNER]
    if admin_system.OWNER_ID is None and not owners:
        _err(lines, "No Owner detected (OWNER_ID env var is unset and no level-1 admin in DB)")
    else:
        _ok(lines, "At least 1 Owner exists")

    valid_levels = {
        admin_system.LEVEL_SUPER_OWNER,
        admin_system.LEVEL_SENIOR_ADMIN,
        admin_system.LEVEL_MODERATOR,
        admin_system.LEVEL_SUPPORT_STAFF,
    }
    invalid = [a for a in admins if a[1] not in valid_levels]
    if invalid:
        _err(lines, f"Invalid admin level(s) found for user_id(s): {[a[0] for a in invalid]}")
    else:
        _ok(lines, "All admin levels are valid (no corrupt permission levels)")

    try:
        # یک smoke-test ساده برای اطمینان از این‌که توابع مجوز کرش نمی‌کنند
        admin_system.has_permission(0, "view_stats")
        admin_system.can_manage_admins(0)
        _ok(lines, "Permission system loads correctly")
    except Exception as e:
        _err(lines, f"Permission system error: {e}")

    # هشدار اگر هیچ usage log ای امروز ثبت نشده (احتمال خرابی log_usage)
    try:
        daily = admin_system.get_daily_stats()
        if daily["total_starts"] == 0:
            _warn(lines, "No usage logs (/start) found for today")
        else:
            _ok(lines, f"Usage logs found for today ({daily['total_starts']} starts)")
    except Exception as e:
        _err(lines, f"Usage stats check failed: {e}")


def _check_runtime_health(lines, application=None):
    """ثبت هندلرها (در صورت در دسترس بودن شیء Application)."""
    if application is None:
        _warn(lines, "Application instance not provided — handler registration check skipped")
        return

    try:
        handler_count = sum(len(group) for group in application.handlers.values())
        if handler_count == 0:
            _err(lines, "No handlers registered on the Application (bot would not respond)")
        else:
            _ok(lines, f"{handler_count} handler(s) registered")
    except Exception as e:
        _warn(lines, f"Could not inspect registered handlers: {e}")


def _check_state_health(lines, application=None):
    """فلگ‌های گیرکرده (orphaned pending states) در user_data همه‌ی کاربران."""
    if application is None:
        _warn(lines, "Application instance not provided — stuck-state scan skipped")
        return

    stuck_flags = ("awaiting_new_admin", "awaiting_transfer_owner", "voice_staff")
    stuck_users = []

    try:
        for uid, udata in application.user_data.items():
            if not isinstance(udata, dict):
                continue
            if any(udata.get(flag) for flag in stuck_flags):
                stuck_users.append(uid)
    except Exception as e:
        _warn(lines, f"Stuck-state scan failed: {e}")
        return

    if stuck_users:
        _warn(lines, f"{len(stuck_users)} user(s) have a pending/awaiting state flag set: {stuck_users}")
    else:
        _ok(lines, "No stuck user_data flags detected")


def run_system_diagnostics(application=None) -> str:
    """
    اجرای کامل تشخیص سیستم. فقط on-demand فراخوانی می‌شود (هرگز در حلقه‌ی
    اصلی یا هندلرهای معمولی ربات اجرا نمی‌شود) تا هیچ تاثیری روی کارایی
    اجرای عادی ربات نداشته باشد.

    application: شیء telegram.ext.Application (اختیاری) - برای بررسی
    هندلرهای ثبت‌شده و حالت‌های گیرکرده‌ی کاربران. اگر داده نشود، آن دو
    بخش با [WARNING] نشانه‌گذاری می‌شوند (نه [ERROR]، چون نبود آن باگ نیست).
    """
    lines = []

    _check_database_health(lines)
    _check_admin_system_health(lines)
    _check_runtime_health(lines, application)
    _check_state_health(lines, application)

    error_count = sum(1 for l in lines if l.startswith("[ERROR]"))
    warning_count = sum(1 for l in lines if l.startswith("[WARNING]"))

    summary = f"\nSummary: {error_count} error(s), {warning_count} warning(s)"
    return "\n".join(lines) + summary
