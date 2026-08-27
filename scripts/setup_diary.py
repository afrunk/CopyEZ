"""
BondageDiary 初始化脚本

用法：
    python scripts/setup_diary.py            # 创建两个角色（master / pup）
    python scripts/setup_diary.py --force    # 强制重置两个角色的密码
    python scripts/setup_diary.py --master   # 只重置主人密码
    python scripts/setup_diary.py --pup      # 只重置母狗密码

功能：
    - 自动创建 DiaryUser(master) + DiaryUser(pup)
    - 生成随机强密码，写到 instance/diary_init_passwords.txt
    - 不会打印到终端（隐私）
    - 设置 must_change_password=True（首次登录强制改密）
"""
import os
import sys
import argparse

# 让脚本能从项目根目录导入 app.*
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.extensions import db
from app.models.bondage_diary import DiaryUser
from app.modules.bondage_diary.security import generate_strong_password


def init_user(role: str, force: bool = False) -> DiaryUser:
    """初始化一个角色账号。返回 DiaryUser（含明文密码，通过 user._plain_password 暂存）"""
    user = DiaryUser.query.filter_by(role=role).first()

    if user and not force:
        print(f"[跳过] {role} 账号已存在（id={user.id}）。如需重置请加 --force 或 --{role}")
        return None

    plain_pwd = generate_strong_password(length=12)

    if user is None:
        if role == "master":
            display_name = "主人"
        else:
            display_name = "母狗"
        user = DiaryUser(
            display_name=display_name,
            role=role,
            is_active=True,
        )
        db.session.add(user)

    user.set_password(plain_pwd)  # set_password 已清 must_change_password
    user.must_change_password = True  # 强制首次改密
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()

    # 暂存明文密码（不存数据库，仅用于写文件）
    user._plain_password = plain_pwd
    return user


def write_passwords_file(users_with_pwd: list) -> str:
    """写入 instance/diary_init_passwords.txt"""
    instance_dir = os.path.join(PROJECT_ROOT, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    file_path = os.path.join(instance_dir, "diary_init_passwords.txt")

    lines = [
        "=" * 50,
        "BondageDiary 初始密码（请妥善保管，删除此文件前请先记住）",
        "=" * 50,
        "",
    ]
    for u in users_with_pwd:
        lines.append(f"角色: {u.role} ({u.display_name})")
        lines.append(f"密码: {u._plain_password}")
        lines.append("")

    lines.append("=" * 50)
    lines.append("注意：首次登录会强制要求修改密码。")
    lines.append("      密码强度：≥10位，含大小写字母、数字、特殊字符。")
    lines.append("=" * 50)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # 设文件权限为仅当前用户可读（类 Unix 系统有效）
    try:
        os.chmod(file_path, 0o600)
    except Exception:
        pass

    return file_path


def main():
    parser = argparse.ArgumentParser(description="BondageDiary 初始化")
    parser.add_argument("--force", action="store_true", help="强制重置已存在角色的密码")
    parser.add_argument("--master", action="store_true", help="只重置主人密码")
    parser.add_argument("--pup", action="store_true", help="只重置母狗密码")
    args = parser.parse_args()

    # 决定要处理哪些角色
    if args.master:
        roles = ["master"]
    elif args.pup:
        roles = ["pup"]
    else:
        roles = ["master", "pup"]

    # 启动 Flask app context
    try:
        from app import create_app
        application = create_app()
    except (ImportError, AttributeError):
        # 旧版 app.py 没有 factory 函数，走 importlib 顶层加载
        import importlib.util
        spec = importlib.util.spec_from_file_location("top_app", os.path.join(PROJECT_ROOT, "app.py"))
        top = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(top)
        application = top.app

    with application.app_context():
        users_with_pwd = []
        for role in roles:
            u = init_user(role, force=args.force)
            if u is not None:
                users_with_pwd.append(u)
                print(f"[完成] {role}: id={u.id}, display_name={u.display_name}")

        if users_with_pwd:
            file_path = write_passwords_file(users_with_pwd)
            print(f"\n密码已写入: {file_path}")
            print("(出于隐私考虑，明文密码不在终端显示)")
        else:
            print("\n无变更。")


if __name__ == "__main__":
    main()
