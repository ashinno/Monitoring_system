import sqlite3
from database import SQLALCHEMY_DATABASE_URL

def migrate():
    db_path = "../sentinel.db" # Assumes running from backend/ and db is in root
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add columns to settings table
    columns = [
        ("smtp_server", "VARCHAR"),
        ("smtp_port", "INTEGER"),
        ("smtp_username", "VARCHAR"),
        ("smtp_password", "VARCHAR"),
        ("sms_notifications", "BOOLEAN DEFAULT 0"),
        ("twilio_account_sid", "VARCHAR"),
        ("twilio_auth_token", "VARCHAR"),
        ("twilio_from_number", "VARCHAR"),
        ("twilio_to_number", "VARCHAR")
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE settings ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            print(f"Column {col_name} might already exist: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
