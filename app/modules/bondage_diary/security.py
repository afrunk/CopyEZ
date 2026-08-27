"""
BondageDiary security helpers.

- 密码策略：强度校验
- 错误响应时间延迟（防时序攻击）
- 失败锁定：单 IP / 单角色双维度
- 角色识别：根据密码哈希比对识别 master / pup（不告诉调用方是谁）
"""
from __future__ import annotations

import re
import time
import random
import string
from datetime import timedelta
from typing import Optional, Tuple

from app.extensions import db
from app.models.bondage_diary import DiaryUser, DiaryLoginAttempt
from app.utils.datetime_utils import now_bj

# ── 阈值配置 ────────────────────────────────────────────────────────────────
SOFT_LOCK_IP_FAILS = 5            # 单 IP 15 分钟内失败 5 次 → 软锁
SOFT_LOCK_IP_WINDOW = timedelta(minutes=15)
ROLE_LOCK_FAILS = 10              # 单角色 1 小时内失败 10 次 → 角色锁
ROLE_LOCK_WINDOW = timedelta(hours=1)
SOFT_LOCK_DURATION_MIN = 15       # 软锁持续 15 分钟
ROLE_LOCK_DURATION_MIN = 60       # 角色锁持续 60 分钟
RESPONSE_DELAY_MS = 800           # 登录失败响应延迟（防时序攻击）

# ── 密码强度 ────────────────────────────────────────────────────────────────
MIN_PASSWORD_LEN = 10
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$"
)

GENERIC_LOGIN_ERROR = "密码错误或角色不存在"


def password_strength_ok(raw: str) -> Tuple[bool, str]:
    """检查密码强度，返回 (ok, reason)"""
    if not raw or len(raw) < MIN_PASSWORD_LEN:
        return False, f"密码至少 {MIN_PASSWORD_LEN} 位"
    if not PASSWORD_PATTERN.match(raw):
        return False, "密码必须包含大小写字母、数字、特殊字符"
    return True, ""


def generate_strong_password(length: int = 12) -> str:
    """生成符合强度要求的随机密码"""
    # 保证四类字符各至少一个
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()-_=+[]{};:,.?"
    pool = lower + upper + digits + symbols

    chars = [
        random.choice(lower),
        random.choice(upper),
        random.choice(digits),
        random.choice(symbols),
    ]
    for _ in range(length - 4):
        chars.append(random.choice(pool))
    random.shuffle(chars)
    return "".join(chars)


def fake_delay() -> None:
    """登录失败时的延迟（无论结果如何都强制走）"""
    # 加一点随机抖动（±100ms），让攻击者更难通过时序判断
    jitter = random.uniform(0, 0.1)
    target = (RESPONSE_DELAY_MS + jitter * 100) / 1000.0
    time.sleep(target)


def record_login_attempt(attempted_role: Optional[str], ip: Optional[str], success: bool) -> None:
    """写入登录审计"""
    attempt = DiaryLoginAttempt(
        attempted_role=attempted_role,
        ip_address=ip,
        success=success,
    )
    db.session.add(attempt)
    db.session.commit()


def ip_is_soft_locked(ip: Optional[str]) -> bool:
    """检查 IP 是否处于软锁状态"""
    if not ip:
        return False
    window_start = now_bj() - SOFT_LOCK_IP_WINDOW
    fail_count = DiaryLoginAttempt.query.filter(
        DiaryLoginAttempt.ip_address == ip,
        DiaryLoginAttempt.success == False,  # noqa: E712
        DiaryLoginAttempt.created_at >= window_start,
    ).count()
    return fail_count >= SOFT_LOCK_IP_FAILS


def ip_lock_until(ip: Optional[str]) -> Optional[float]:
    """IP 软锁到期时间戳（最早一次失败 + 15min），未锁返回 None"""
    if not ip:
        return None
    window_start = now_bj() - SOFT_LOCK_IP_WINDOW
    earliest = DiaryLoginAttempt.query.filter(
        DiaryLoginAttempt.ip_address == ip,
        DiaryLoginAttempt.success == False,  # noqa: E712
        DiaryLoginAttempt.created_at >= window_start,
    ).order_by(DiaryLoginAttempt.created_at.asc()).first()
    if not earliest:
        return None
    fail_count = DiaryLoginAttempt.query.filter(
        DiaryLoginAttempt.ip_address == ip,
        DiaryLoginAttempt.success == False,  # noqa: E712
        DiaryLoginAttempt.created_at >= earliest.created_at,
    ).count()
    if fail_count >= SOFT_LOCK_IP_FAILS:
        lock_until = earliest.created_at + timedelta(minutes=SOFT_LOCK_DURATION_MIN)
        return lock_until.timestamp()
    return None


def user_is_locked(user: DiaryUser) -> bool:
    return user.is_locked()


def authenticate_by_credentials(raw_username: str, raw_password: str) -> Optional[DiaryUser]:
    """
    根据账号+密码识别用户。

    调用方必须：
    - 无论成功失败都调 fake_delay()
    - 用通用错误信息返回
    """
    if not raw_username or not raw_password:
        return None
    user = DiaryUser.query.filter_by(
        username=raw_username.strip(), is_active=True,
    ).first()
    if not user:
        return None
    if user.is_locked():
        return None
    if user.check_password(raw_password):
        return user
    return None


def authenticate_by_password(raw_password: str) -> Optional[DiaryUser]:
    """
    根据密码识别用户。
    遍历所有 DiaryUser，校验密码哈希。
    返回匹配的用户（或 None）。

    ⚠️ 调用方必须：
    - 无论成功失败都调 fake_delay()
    - 用通用错误信息返回
    """
    if not raw_password:
        return None
    users = DiaryUser.query.filter_by(is_active=True).all()
    for u in users:
        if u.is_locked():
            continue  # 已锁定的跳过（但不告诉调用方）
        if u.check_password(raw_password):
            return u
    return None


def increment_user_fail(user: DiaryUser) -> None:
    """用户级失败计数（用于角色锁）"""
    user.failed_attempts = (user.failed_attempts or 0) + 1
    if user.failed_attempts >= ROLE_LOCK_FAILS:
        user.lock_for_minutes(ROLE_LOCK_DURATION_MIN)
    db.session.commit()


def reset_user_fail(user: DiaryUser) -> None:
    """登录成功后清零失败计数"""
    if user.failed_attempts:
        user.failed_attempts = 0
        db.session.commit()
