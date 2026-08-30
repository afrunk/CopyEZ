"""
Application configuration - Flask settings, DB URI, secrets.

Only stores runtime configuration. Static reference data lives in app/utils/presets.py.
"""

import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("COPYEZ_SECRET_KEY", "copyez-secret-key")

    # ── Web Push VAPID（WeChat 消息推送，iOS Safari PWA 必需） ──────────
    # 公钥:前端 Service Worker 拿去做 applicationServerKey
    # 私钥:服务端 webpush() 签名用，请勿外泄
    VAPID_PUBLIC_KEY = os.environ.get(
        "COPYEZ_VAPID_PUBLIC_KEY",
        "BLvwa3ImfCpzzGKE4Dxixw_PuQBmVrhSMCHaV9Y339sP5d_U_xxAMq-2vpBGuUdZZ49uVyuqXqFJncV2ghroqL4",
    )
    VAPID_PRIVATE_KEY = os.environ.get(
        "COPYEZ_VAPID_PRIVATE_KEY",
        "-----BEGIN PRIVATE KEY-----\n"
        "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgoq6wDfPbhorSEVuB\n"
        "a4OjUzZNAkrh8Ce3bp58VZ/gw2ihRANCAAS78GtyJnwqc8xihOA8YscPz7kAZla4\n"
        "UjAh2lfWN9/bD+Xf1P8cQDKvtr6QRrlHWWePblcrql6hSZ3FdoIa6Ki+\n"
        "-----END PRIVATE KEY-----\n",
    )
    VAPID_CLAIMS_SUB = os.environ.get(
        "COPYEZ_VAPID_CLAIMS_SUB",
        "mailto:admin@copyez.local",
    )

    # SQLite database in instance/ folder (Flask default behavior)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "copyez.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    TEMPLATES_AUTO_RELOAD = True
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }


class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True


class ProductionConfig(Config):
    DEBUG = False
    TEMPLATES_AUTO_RELOAD = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
