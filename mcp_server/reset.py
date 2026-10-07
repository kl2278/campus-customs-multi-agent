"""Reset the working copy from the original database (never writes to the original)."""

import os
import shutil
import tempfile
from pathlib import Path

from mcp_server.db import ORIGINAL_DB_PATH, WriteRefused, _is_original, get_db_path


def reset_working_copy() -> Path:
    """Replace the working copy with a fresh copy of the original, atomically.

    Copies the original to a temporary file next to the target, then replaces the
    target in one step, and removes stale -wal/-shm files. The lazily created
    tables (approvals, purchase orders, drafts) disappear with the old file.
    Refuses if the target path is the original.
    """
    target = get_db_path()
    if _is_original(target):
        raise WriteRefused("Refusing to reset: the target path resolves to the original database.")
    if not ORIGINAL_DB_PATH.exists():
        raise WriteRefused("The original database was not found.")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".reset-", suffix=".db")
    os.close(fd)
    try:
        shutil.copyfile(ORIGINAL_DB_PATH, tmp)  # read-only use of the original
        os.replace(tmp, target)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    for suffix in ("-wal", "-shm"):
        stale = Path(str(target) + suffix)
        if stale.exists():
            stale.unlink()
    return target
