import os
from db import Session, FileIndex, WatchedRoot

# Still list any absolute prefixes you want to skip entirely...
EXCLUDE_PREFIXES = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\Users\conno\AppData"
    r"D:\Programs"
    r"D:\GTAMODS"
    r"D:\Oculus"
    r"D:\PrehistoricWorldMods"
    r"D:\\3DModels"
]

def should_skip(path: str) -> bool:
    # normalize case & separators
    p = os.path.normcase(os.path.normpath(path))

    # 1) skip any path containing "venv"
    if "venv" in p:
        return True

    # 2) skip any of your hard-coded prefixes
    for ex in EXCLUDE_PREFIXES:
        if p.startswith(os.path.normcase(ex)):
            return True

    return False

def index_root(root_path: str):
    session = Session()
    for dirpath, dirs, files in os.walk(root_path, topdown=True):
        # If the current directory should be skipped entirely:
        if should_skip(dirpath):
            dirs[:] = []   # don’t descend into its children
            continue

        # Prune any dirs that match skip
        dirs[:] = [d for d in dirs
                   if not should_skip(os.path.join(dirpath, d))]

        for name in dirs + files:
            full = os.path.join(dirpath, name)
            if should_skip(full):
                continue

            stat = os.stat(full)
            meta = {"size": stat.st_size, "mtime": stat.st_mtime}

            entry = session.query(FileIndex).filter_by(path=full).first()
            if entry:
                entry.is_dir    = os.path.isdir(full)
                entry.file_meta = meta
            else:
                session.add(FileIndex(
                    path     = full,
                    is_dir   = os.path.isdir(full),
                    file_meta= meta
                ))
    session.commit()

if __name__ == "__main__":
    session = Session()
    for wr in session.query(WatchedRoot).all():
        print(f"Indexing {wr.root} …")
        index_root(wr.root)
