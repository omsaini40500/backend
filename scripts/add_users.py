import uuid
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.models import User, Department, Team
from passlib.context import CryptContext
from datetime import datetime, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

db = SessionLocal()

def get_or_create_dept(dept_id):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        dept = Department(id=dept_id, name=dept_id)
        db.add(dept)
        db.commit()
        db.refresh(dept)
    return dept.id

def get_or_create_team(name, dept_id):
    if not name: return None
    team = db.query(Team).filter(Team.name == name, Team.department_id == dept_id).first()
    if not team:
        team = Team(id=str(uuid.uuid4()), name=name, department_id=dept_id)
        db.add(team)
        db.commit()
        db.refresh(team)
    return team.id

# Create/Get departments and teams
dept_d3 = get_or_create_dept("d3")
team_photographer = get_or_create_team("photographer", dept_d3)

dept_d6 = get_or_create_dept("d6")
team_founder = get_or_create_team("Founder", dept_d6)

users_to_add = [
    {
        "name": "Jaskaran Singh Kohli",
        "email": "jaskaransinghkohli17@gmail.com",
        "role": "member",
        "dept_id": dept_d3,
        "team_id": team_photographer
    },
    {
        "name": "Manas",
        "email": "manas@flashdigital.in",
        "role": "super_admin",
        "dept_id": dept_d6,
        "team_id": team_founder
    },
    {
        "name": "Aakash",
        "email": "aakash@flashdigital.in",
        "role": "super_admin",
        "dept_id": dept_d6,
        "team_id": None
    }
]

default_password = "demo"

for user_data in users_to_add:
    existing = db.query(User).filter(User.email == user_data["email"]).first()
    if existing:
        print(f"Updating user {user_data['name']} with department and role...")
        existing.role = user_data["role"]
        existing.department_id = user_data["dept_id"]
        existing.team_id = user_data["team_id"]
    else:
        new_user = User(
            id=str(uuid.uuid4()),
            name=user_data["name"],
            email=user_data["email"],
            role=user_data["role"],
            department_id=user_data["dept_id"],
            team_id=user_data["team_id"],
            hashed_password=get_password_hash(default_password),
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_user)
        print(f"Added user {user_data['name']} ({user_data['email']}) as {user_data['role']}")

# Update Arisha Naaz
arisha = db.query(User).filter(User.name.ilike("%Arisha Naaz%")).first()
if arisha:
    arisha.role = "admin"
    print(f"Updated Arisha Naaz's role to admin (Found email: {arisha.email})")
else:
    print("Could not find Arisha Naaz in the database.")

db.commit()
db.close()
print("Users successfully added/updated with departments and teams.")
