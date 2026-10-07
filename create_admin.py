from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User(
        username="admin",
        email="admin@example.com",  # ✅ Make sure this is not None
        password=generate_password_hash("admin123"),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin user created successfully.")
