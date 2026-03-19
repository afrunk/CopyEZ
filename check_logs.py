import urllib.request, json

data = urllib.request.urlopen("http://127.0.0.1:5000/api/logs").read().decode()
payload = json.loads(data)
if isinstance(payload, dict):
    logs = payload.get("events", [])
    keys = payload.get("contract_signed_keys", [])
    print(f"共 {len(logs)} 条事件，契约已签署分组键: {keys}")
else:
    logs = payload
    print(f"共 {len(logs)} 条记录")
for item in logs[:5]:
    print(item)
