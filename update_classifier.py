# update_classifier.py

import json
from main import llm
from db import Session, Project
from context_fetchers import set_user_info

def classify_update_intent(text: str) -> dict:
    """
    Ask the LLM if this message should update user_info or create a new project.
    Returns a dict:
      { "update_type": "user_info"|"new_project"|None,
        "key": str,           # user_info key
        "value": str,         # new user_info value
        "project": {…}        # dict for new_project
      }
    """
    system = {
        "role": "system",
        "content": (
            "Decide if the user's message should update the database. "
            "If they update personal info, reply exactly:\n"
            '{"update_type":"user_info","key":KEY,"value":VALUE}\n'
            "If they define a new project, reply exactly:\n"
            '{"update_type":"new_project",'
              '"project":{"name":NAME,"description":DESC,"metadata":META}}\n'
            "Otherwise reply:\n"
            '{"update_type":null}\n'
            "No extra text."
        )
    }
    user = {"role": "user", "content": text}
    resp = llm.create_chat_completion(
        messages=[system, user],
        temperature=0
    )["choices"][0]["message"]["content"]
    try:
        return json.loads(resp)
    except Exception:
        return {"update_type": None}

def add_project_entry(proj: dict):
    session = Session()
    # avoid duplicates
    if not session.query(Project).filter_by(name=proj["name"]).first():
        session.add(Project(
            name=proj["name"],
            description=proj.get("description",""),
            metadata=proj.get("metadata",{})
        ))
        session.commit()
