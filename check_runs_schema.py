import sys, sqlite3
p=sys.argv[1]
con=sqlite3.connect(p)
try:
    cur=con.execute("PRAGMA table_info(runs)")
    cols=[(r[1], r[2]) for r in cur.fetchall()]
    print(p, "->", cols)
finally:
    con.close()