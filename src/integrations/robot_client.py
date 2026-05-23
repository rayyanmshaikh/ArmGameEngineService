import os
import requests

ROBOT_URL = os.environ.get('ROBOT_SERVICE_URL')


def send_move_to_robot(payload: dict):
    """Send AI move to robot-arm service. This is a stub; if `ROBOT_SERVICE_URL` is not set, it just logs."""
    if not ROBOT_URL:
        print('ROBOT_SERVICE_URL not configured; skipping send:', payload)
        return None
    resp = requests.post(ROBOT_URL, json=payload, timeout=5)
    resp.raise_for_status()
    return resp.json()
