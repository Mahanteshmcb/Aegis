import sqlite3
p = r'C:\Users\Mahantesh\DevelopmentProjects\Aegis\aegis.db'
print('DB path:', p)
con = sqlite3.connect(p)
cur = con.cursor()
print('tables:')
for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(' -', r[0])
print('\nRecent system_alerts:')
try:
    for r in cur.execute('SELECT id, tenant_id, data, created_at FROM system_alerts ORDER BY id DESC LIMIT 10'):
        print(r)
except Exception as e:
    print('error reading system_alerts:', e)
con.close()
