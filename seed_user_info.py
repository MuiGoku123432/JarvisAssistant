# seed_user_info.py
from db import Session, UserInfo

session = Session()

# Keys you might want to store:
info = {
    "name":                    "Connor Fancher",
    "age":                     "19",
    "location":                "Omaha, Arkansas, USA and Keller, Texas, USA",
    "timezone":                "America/Chicago",
    "preferred_language":      "en",
    "occupation":              "Software Engineer",
    "employer":                "Windstream",
    "internship":              "Software Engineer Intern at Lockheed Martin",
    "education":               "Pursuing AI degree at Arkansas State University",
    "faith_identity":          "Son of God, disciple of Jesus",
    "relationship_status":     "Committed relationship, planning to propose",
    "salary":                  "$62,000 per year",
    "monthly_takehome":        "$4,000",
    "savings_rate":            "50% of income",
    "savings_account":         "Capital One 360 Performance Savings",
    "height":                  "6\'2\"",
    "weight":                  "205 lbs",
    "body_fat_percentage":     "12-14%",
    "diet":                    "Animal-based (eggs, beef, venison, organ meats, fruit, honey, occasional nuts & avocados)",
    "workout_routine":         "Push–Pull–Legs split, 3–4×/week",
    "current_projects_focus":  "Predator Helmet & Armor, Jarvis AI Assistant, Mountain Meadows website"
}

for key, val in info.items():
    rec = session.query(UserInfo).filter_by(user_key=key).first()
    if rec:
        rec.user_value = val
        print(f"Updated user_info: {key} = {val}")
    else:
        session.add(UserInfo(user_key=key, user_value=val))
        print(f"Added user_info: {key} = {val}")

session.commit()
print("✅ user_info table seeded.")
