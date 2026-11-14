"""
Deploy script: SSH to server, git pull, run migration, restart Flask.
All output uses sys.stdout.buffer to avoid Windows GBK encoding crashes.

凭据来源（按优先级）:
  1. 环境变量 COPYEZ_DEPLOY_PASSWORD / COPYEZ_DEPLOY_HOST / COPYEZ_DEPLOY_USER
  2. 项目根目录 .env 文件中的同名键
服务器密码不再硬编码在源码中。
"""
import os
import sys
import io
import paramiko

# Force UTF-8 for stdout (Windows GBK can't print emoji)
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv(path):
    """极简 .env 解析：KEY=VALUE，忽略 # 注释与空行"""
    values = {}
    if not os.path.exists(path):
        return values
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


_dotenv = _load_dotenv(os.path.join(BASE_DIR, ".env"))


def _setting(name, default=None):
    """环境变量优先，其次 .env，最后默认值"""
    return os.environ.get(name) or _dotenv.get(name) or default


HOST = _setting("COPYEZ_DEPLOY_HOST", "39.106.147.188")
PORT = int(_setting("COPYEZ_DEPLOY_PORT", "22"))
USER = _setting("COPYEZ_DEPLOY_USER", "root")
PASSWORD = _setting("COPYEZ_DEPLOY_PASSWORD")

# Pure-ASCII deploy script (no emoji, no CJK)
# 端口约定: 5000 = haproxy(对外入口), 5001 = Flask(copyez.service), 8443/8080 = nginx
DEPLOY_SCRIPT = r"""#!/bin/bash
set -e

cd /root/CopyEZ

echo "==== [1] git fetch + reset --hard ===="
git fetch origin
git reset --hard origin/main
echo "--- latest commit ---"
git log --oneline -1

echo ""
echo "==== [2] backup db ===="
cp instance/copyez.db instance/copyez.db.bak.$(date +%s) 2>/dev/null || echo "(no db to backup)"

echo ""
echo "==== [3] activate venv ===="
source /root/CopyEZ/venv/bin/activate
which python
python --version

echo ""
echo "==== [4] ensure deps ===="
pip install -q pywebpush==2.5.0 cryptography==50.0.1 || true
python -c "import pywebpush" && echo "[OK] pywebpush installed"

echo ""
echo "==== [5] run wechat migration ===="
python scripts/migrate_wechat.py

echo ""
echo "==== [6] restart copyez.service ===="
systemctl restart copyez
sleep 5
systemctl is-active copyez
systemctl status copyez --no-pager -l | head -6

echo ""
echo "==== [7] tail app.log ===="
tail -20 app.log

echo ""
echo "==== [8] verify ports ===="
echo "-- flask (5001) --"
ss -lntp 2>/dev/null | grep 5001 || echo "(flask NOT listening on 5001)"
echo "-- haproxy (5000) --"
ss -lntp 2>/dev/null | grep 5000 || echo "(haproxy NOT listening on 5000)"

echo ""
echo "==== [9] smoke test ===="
for p in / /gongwen/ /notes /search; do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5001$p)
  echo "$p -> $code"
done

echo ""
echo "==== DEPLOY DONE ===="
"""


def run_ssh():
    if not PASSWORD:
        print(
            "[FAILED] 未配置服务器密码。请设置环境变量 COPYEZ_DEPLOY_PASSWORD，"
            "或在项目根目录 .env 中写入 COPYEZ_DEPLOY_PASSWORD=...",
            file=sys.stderr,
        )
        sys.exit(1)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"[connect] {USER}@{HOST}:{PORT}", flush=True)
    client.connect(HOST, PORT, USER, PASSWORD, timeout=15)
    print("[OK] connected\n", flush=True)

    print("[step A] upload script", flush=True)
    sftp = client.open_sftp()
    remote_script = "/root/deploy_wechat_fix.sh"
    with sftp.file(remote_script, "w") as f:
        f.write(DEPLOY_SCRIPT)
    sftp.chmod(remote_script, 0o755)
    sftp.close()
    print("[OK] script uploaded\n", flush=True)

    print("[step B] execute on server\n", flush=True)
    print("=" * 60, flush=True)
    stdin, stdout, stderr = client.exec_command(
        f"bash {remote_script} 2>&1",
        timeout=180,
    )
    # paramiko ChannelFile 默认 GBK，需要手动 UTF-8 解码
    try:
        text_stream = io.TextIOWrapper(stdout, encoding="utf-8", errors="replace")
        for line in iter(text_stream.readline, ""):
            print(line.rstrip(), flush=True)
    except Exception as e:
        print(f"[output error] {e}", flush=True)

    print("=" * 60, flush=True)
    print("[done]", flush=True)

    try:
        client.exec_command(f"rm -f {remote_script}", timeout=10)
    except Exception:
        pass

    client.close()


if __name__ == "__main__":
    try:
        run_ssh()
    except Exception as e:
        print(f"[FAILED] {e}", file=sys.stderr)
        sys.exit(1)
