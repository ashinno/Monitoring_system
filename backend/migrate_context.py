import sqlite3

def add_context_columns():
    conn = sqlite3.connect('sentinel.db')
    c = conn.cursor()
    
    try:
        c.execute("ALTER TABLE logs ADD COLUMN current_activity TEXT")
        print("Added current_activity column")
    except Exception as e:
        print(f"Column current_activity might already exist: {e}")
        
    try:
        c.execute("ALTER TABLE logs ADD COLUMN activity_summary TEXT")
        print("Added activity_summary column")
    except Exception as e:
        print(f"Column activity_summary might already exist: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_context_columns()
