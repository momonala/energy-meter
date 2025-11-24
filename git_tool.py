import logging
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_TO_COMMIT = "data/energy.db"
BRANCH = "main"


def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


def commit_db_if_changed():
    diff = run_command(["git", "diff", FILE_TO_COMMIT])
    if diff:
        run_command(["git", "add", FILE_TO_COMMIT])
        run_command(["git", "commit", "--amend", "--no-edit"])
        run_command(["git", "push", "--force", "origin", BRANCH])
        run_command(["cp", FILE_TO_COMMIT, f"{FILE_TO_COMMIT}.bk"])
        logger.info(f"[{datetime.now()}] Changes amended to last commit.")
    else:
        logger.info(f"[{datetime.now()}] No changes. Skipping commit.")
