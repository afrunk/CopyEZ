"""
Deploy script: SSH to server, git pull, run migration, restart Flask.
All output uses sys.stdout.buffer to avoid Windows GBK encoding crashes.
"""
import sys
import io
import paramiko

# Force UTF-8 for stdout (Windows GBK can't print emoji)
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

HOST = "39.106.147.188"
PORT = 22
USER = "root"
PASSWORD = "4d&cGd$~S8JE94&"

# Pure-ASCII deploy script (no emoji, no CJK)
DEPLOY_SCRIPT = r"""#!/bin/bash
set -e

cd /root/CopyEZ

echo "==== [1] git fetch + reset --hard ===="
git fetch origin
git reset --hard origin/main
echo "--- latest commit ---"
git log --oneline -1

echo ""
echo "==== [2] kill old flask ===="
lsof -i:5000 2>/dev/null || echo "(no port 5000)"
fuser -k 5000/tcp 2>/dev/null || echo "(nothing to kill)"
sleep 2

echo ""
echo "==== [3] git pull ===="
git pull origin main || true
echo "--- latest commit ---"
git log --oneline -1

echo ""
echo "==== [4] activate venv ===="
source /root/CopyEZ/venv/bin/activate
which python
python --version

echo ""
echo "==== [4b] ensure deps ===="
pip install -q pywebpush==2.5.0 cryptography==50.0.1 || true
python -c "import pywebpush" && echo "[OK] pywebpush installed"

echo ""
echo "==== [5] run wechat migration ===="
python scripts/migrate_wechat.py

echo ""
echo "==== [6] start flask (background) ===="
cd /root/CopyEZ
nohup python app.py > app.log 2>&1 &
echo "Flask PID: $!"
sleep 4

echo ""
echo "==== [7] tail app.log ===="
tail -30 app.log

echo ""
echo "==== [8] verify port 5000 ===="
ss -lntp 2>/dev/null | grep 5000 || lsof -i:5000 2>/dev/null || echo "(not listening)"

echo ""
echo "==== DEPLOY DONE ===="
"""


def run_ssh():
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
