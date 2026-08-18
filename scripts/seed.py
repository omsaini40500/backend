import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models import User, Department, Team

def seed_data():
    db = SessionLocal()
    try:
        # ── Departments ──────────────────────────────────────────────────
        if db.query(Department).count() == 0:
            depts = [
                Department(id="d1", name="Technology"),
                Department(id="d2", name="HR & Operations"),
                Department(id="d3", name="Creative"),
                Department(id="d4", name="Performance Marketing"),
                Department(id="d5", name="Social Media"),
                Department(id="d6", name="Business Development"),
                Department(id="d7", name="Finance"),
            ]
            for d in depts:
                db.add(d)
            db.commit()

        # ── Teams ────────────────────────────────────────────────────────
        if db.query(Team).count() == 0:
            teams_data = [
                Team(id="t1", name="Tech Team",          department_id="d1"),
                Team(id="t2", name="HR Team",            department_id="d2"),
                Team(id="t3", name="Creative Team",      department_id="d3"),
                Team(id="t4", name="Performance Team",   department_id="d4"),
                Team(id="t5", name="Social Media Team",  department_id="d5"),
                Team(id="t6", name="BizDev Team",        department_id="d6"),
                Team(id="t7", name="Finance Team",       department_id="d7"),
            ]
            for t in teams_data:
                db.add(t)
            db.commit()

        # ── Users ────────────────────────────────────────────────────────
        if db.query(User).count() == 0:
            users_data = [
                {"id": "u1",  "name": "Durga Prasad Naithani", "email": "akshaynaithani@gmail.com",    "job": "Web Developer",                      "role": "admin",          "dept": "d1", "team": "t1"},
                {"id": "u2",  "name": "Arisha Naaz",           "email": "arishanaaz2001@gmail.com",    "job": "HR Manager",                         "role": "project_manager","dept": "d2", "team": "t2"},
                {"id": "u3",  "name": "Aman Ali",              "email": "amaanali09999@gmail.com",     "job": "Video Editor",                       "role": "member",         "dept": "d3", "team": "t3"},
                {"id": "u4",  "name": "Aditya",                "email": "idadityaweb@gmail.com",       "job": "Performance Marketing Manager",      "role": "team_leader",    "dept": "d4", "team": "t4"},
                {"id": "u5",  "name": "Rahul Chauhan",         "email": "rt8422728@gmail.com",         "job": "Performance Marketing Manager",      "role": "team_leader",    "dept": "d4", "team": "t4"},
                {"id": "u6",  "name": "Ritika Singh",          "email": "ratika36364@gmail.com",       "job": "Social Media Manager",               "role": "team_leader",    "dept": "d5", "team": "t5"},
                {"id": "u7",  "name": "Pratham Bhandari",      "email": "prathamworkk1@gmail.com",     "job": "Business Development Manager",       "role": "project_manager","dept": "d6", "team": "t6"},
                {"id": "u8",  "name": "Gitesh Singh",          "email": "singhgitesh24@gmail.com",     "job": "Accountant",                         "role": "member",         "dept": "d7", "team": "t7"},
                {"id": "u9",  "name": "Om Saini",              "email": "omsaini40500@gmail.com",      "job": "Software Engineer Intern",           "role": "super_admin",    "dept": "d1", "team": "t1"},
                {"id": "u10", "name": "Harshnoor Singh",       "email": "harshnoorsingh0406@gmail.com","job": "Content Writer Intern",              "role": "member",         "dept": "d3", "team": "t3"},
                {"id": "u11", "name": "Arshpreet Kaur",        "email": "arshkaur0306@gmail.com",      "job": "Influencer Marketing Intern",        "role": "member",         "dept": "d5", "team": "t5"},
                {"id": "u12", "name": "Tanishka Kesari",       "email": "kesaritanishka@gmail.com",    "job": "Content Creator Intern",             "role": "member",         "dept": "d3", "team": "t3"},
                {"id": "u13", "name": "Sandhya Kumari",        "email": "singhsandhya2232@gmail.com",  "job": "Accountant",                         "role": "member",         "dept": "d7", "team": "t7"},
                {"id": "u14", "name": "Namya Gandhi",          "email": "namya.gandhi31@gmail.com",    "job": "Senior Graphic Designer Executive",  "role": "member",         "dept": "d3", "team": "t3"},
            ]
            for u in users_data:
                user = User(
                    id=u["id"],
                    name=u["name"],
                    email=u["email"],
                    hashed_password=get_password_hash("demo"),
                    role=u["role"],
                    department_id=u.get("dept"),
                    team_id=u.get("team"),
                    client_id=u.get("client_id"),
                    is_active=True,
                )
                db.add(user)
            db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding data...")
    seed_data()
    print("Data seeding completed!")
