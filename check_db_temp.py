import sqlite3
conn = sqlite3.connect('copyez.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', [r[0] for r in cursor.fetchall()])

try:
    cursor.execute('SELECT COUNT(*) FROM visit_log')
    print('visit_log count:', cursor.fetchone()[0])
    cursor.execute('SELECT * FROM visit_log ORDER BY id DESC LIMIT 5')
    print('Last 5 visit_log records:')
    for row in cursor.fetchall():
        print(row)
except Exception as e:
    print('Error:', e)

try:
    cursor.execute('SELECT COUNT(*) FROM visit_alias')
    print('visit_alias count:', cursor.fetchone()[0])
except Exception as e:
    print('visit_alias error:', e)

conn.close()
