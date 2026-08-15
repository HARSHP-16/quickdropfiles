"""Deploy as a separate Azure Functions timer app; set DATABASE_URL and storage variables."""
import logging
import os
import sys
from pathlib import Path
import azure.functions as func

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app import create_app
from backend.services.cleanup_service import cleanup_expired

app = func.FunctionApp()

@app.schedule(schedule="0 */5 * * * *", arg_name="timer", use_monitor=True)
def cleanup_expired_shares(timer: func.TimerRequest) -> None:
    flask_app = create_app()
    with flask_app.app_context():
        count = cleanup_expired(flask_app.extensions["storage"])
        logging.info("QuickDrop cleanup processed %s expired shares", count)
