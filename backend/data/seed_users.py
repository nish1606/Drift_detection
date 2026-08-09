from sqlalchemy.orm import Session

from backend.core.auth import get_password_hash
from backend.database.models import User


def seed_users(db: Session):
    users = [
        {"username": "analyst", "password": "analyst123", "role": "Analyst", "display_name": "Analyst User"},
        {"username": "risk_engineer", "password": "risk123", "role": "RiskEngineer", "display_name": "Risk Engineer"},
        {"username": "compliance", "password": "compliance123", "role": "Compliance", "display_name": "Compliance User"},
    ]
    for u in users:
        if not db.query(User).filter(User.username == u["username"]).first():
            db.add(User(username=u["username"], display_name=u["display_name"], password_hash=get_password_hash(u["password"]), role=u["role"]))
    db.commit()
