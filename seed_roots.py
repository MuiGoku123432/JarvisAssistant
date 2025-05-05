# seed_roots.py
from db import Session, WatchedRoot

session = Session()

# Change these to whichever folders you want indexed.
# On Windows Python, use Windows paths:
roots = [
    r"D:\\"
]


for path in roots:
    exists = session.query(WatchedRoot).filter_by(root=path).first()
    if not exists:
        session.add(WatchedRoot(root=path))
        print(f"Added watched root: {path}")
    else:
        print(f"Already watching: {path}")

session.commit()
