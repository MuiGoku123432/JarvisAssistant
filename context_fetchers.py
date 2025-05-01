# context_fetchers.py
from db import Session, Project, UserInfo

_session = Session()

def fetch_projects(limit: int = 5):
    return _session.query(Project) \
                   .order_by(Project.created_at.desc()) \
                   .limit(limit) \
                   .all()

def get_user_info(key: str, default: str = "") -> str:
    record = _session.query(UserInfo) \
                     .filter_by(user_key=key) \
                     .first()
    return record.user_value if record else default

def set_user_info(key: str, value: str):
    rec = _session.query(UserInfo).filter_by(user_key=key).first()
    if rec:
        rec.user_value = value
    else:
        rec = UserInfo(user_key=key, user_value=value)
        _session.add(rec)
    _session.commit()
