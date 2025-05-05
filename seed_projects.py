# seed_projects.py
from db import Session, Project

session = Session()

# Define the projects you want to add
projects = [
    {
        "name": "Jarvis AI Assistant",
        "description": "A local LLM-driven desktop assistant with file and system integration.",
        "proj_meta": {"status": "active", "priority": "high"}
    },
    {
        "name": "Mountain Meadows Website",
        "description": "React/MUI site for the Mountain Meadows Massacre Foundation.",
        "proj_meta": {"status": "wip", "tech": ["React", "Supabase", "Vercel"]}
    },
        {
        "name": "Predator Helmet Project",
        "description": (
            "Design and build a Predator-inspired helmet using carbon fiber "
            "composite. Features include an integrated HUD overlay from dual "
            "FLIR Lepton thermal cameras and RGB cameras, OpenCV-based video "
            "processing on a Jetson Nano, and a lightweight exoskeletal "
            "mount for helmet stabilization."
        ),
        "proj_meta": {
            "status": "WIP",
            "priority": "high",
            "components": ["Carbon Fiber", "FLIR Lepton", "Jetson Nano", "OpenCV"],
            "start_date": "2025-04-01"
        }
    },
    {
        "name": "Predator Armor Project",
        "description": (
            "Construct a full-body Predator-style armor set using carbon fiber "
            "composite panels over a shape-memory alloy exoskeleton. "
            "Internally lined with artificial muscle actuators for enhanced "
            "mobility, integrated power and data routing for HUD and sensors, "
            "and modular attachment points for additional gear."
        ),
        "proj_meta": {
            "status": "planning",
            "priority": "medium",
            "materials": ["Carbon Fiber", "Shape-Memory Alloy", "DEA Actuators"],
            "estimated_completion": "2025-12-31"
        }
    },
    # add as many as you like...
]

for p in projects:
    # Avoid duplicates
    exists = session.query(Project).filter_by(name=p["name"]).first()
    if not exists:
        proj = Project(
            name=p["name"],
            description=p["description"],
            proj_meta=p["proj_meta"]
        )
        session.add(proj)
        print(f"Added project: {p['name']}")
    else:
        print(f"Project already exists: {p['name']}")

session.commit()
print("✅ Projects table seeded.")
