import sqlite3
p='C:/Users/Mahantesh/DevelopmentProjects/Aegis/aegis.db'
con=sqlite3.connect(p)
cur=con.cursor()
for r in cur.execute('SELECT id, task_id, status, assigned_robot_id, assigned_time, updated_at FROM scheduled_robotic_tasks ORDER BY id DESC LIMIT 5'):
    print(r)
con.close()
