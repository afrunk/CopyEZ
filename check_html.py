import urllib.request, re
html = urllib.request.urlopen("http://127.0.0.1:5000/monitor").read().decode("utf-8")
# 找第一个 script 块（内联 JS）
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for s in scripts:
    s = s.strip()
    if s and 'loadLogs' in s:
        # 打印前 10 行
        lines = s.split('\n')
        for i, line in enumerate(lines[:10], 1):
            print(f"{i}: {line}")
        break
