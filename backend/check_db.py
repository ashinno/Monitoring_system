from database import SessionLocal
import models
import auth

db = SessionLocal()
users = db.query(models.User).all()
print(f"Users found: {len(users)}")
for u in users:
    print(f"User: {u.name}, ID: {u.id}, Hash: {u.hashed_password}")
    # Verify password
    if u.id == "admin":
        print(f"Verifying 'admin' password: {auth.verify_password('admin', u.hashed_password)}")

db.close()
