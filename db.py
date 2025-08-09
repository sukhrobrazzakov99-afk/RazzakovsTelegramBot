import sqlite3, pathlib
DB_PATH = pathlib.Path('data.sqlite3')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        user_name TEXT,
        type TEXT,
        category TEXT,
        currency TEXT,
        amount INTEGER,
        ts TEXT
    )''')
    conn.commit()
    conn.close()

def add_op(chat_id:int,user_id:int,user_name:str,op_type:str,category:str,currency:str,amount:int, ts:str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO ops(chat_id,user_id,user_name,type,category,currency,amount,ts) VALUES (?,?,?,?,?,?,?,?)',
              (chat_id,user_id,user_name,op_type,category,currency,amount,ts))
    conn.commit()
    conn.close()

def get_balance(chat_id:int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    res = {'USD':0,'UZS':0}
    c.execute('SELECT type,currency,SUM(amount) FROM ops WHERE chat_id=? GROUP BY type,currency',(chat_id,))
    for t,cur,sumv in c.fetchall():
        if t=='Доход':
            res[cur]=res.get(cur,0)+ (sumv or 0)
        else:
            res[cur]=res.get(cur,0)- (sumv or 0)
    conn.close()
    return res

def get_history(chat_id:int, limit:int=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT type,category,currency,amount,ts,user_name FROM ops WHERE chat_id=? ORDER BY id DESC LIMIT ?',
              (chat_id,limit))
    rows=c.fetchall()
    conn.close()
    return rows
