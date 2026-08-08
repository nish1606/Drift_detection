from sqlalchemy.orm import Session
from backend.database.models import User
from backend.core.auth import get_password_hash

def seed_users(db: Session):
    users = [
        {"username": "analyst", "password": "analyst123", "role": "Analyst"},
        {"username": "risk_engineer", "password": "risk123", "role": "RiskEngineer"},
        {"username": "compliance", "password": "compliance123", "role": "Compliance"},
    ]
    for u in users:
        if not db.query(User).filter(User.username == u["username"]).first():
            db.add(User(username=u["username"], hashed_password=get_password_hash(u["password"]), role=u["role"]))
    db.commit()
