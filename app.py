import json
import logging
import threading

from flask import Flask
from flask import jsonify
from flask import request

from database import get_readings
from database import get_stats
from database import latest_energy_reading
from database import num_energy_readings_last_hour
from database import num_total_energy_readings
from helpers import parse_time_param
from mqtt import get_mqtt_client
from mqtt import mqtt_loop
from scheduler import get_scheduled_jobs
from scheduler import schedule_loop
from values import FLASK_PORT
from values import MQTT_PORT
from values import SERVER_URL
from values import TASMOTA_UI_URL
from values import TOPIC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.WARNING)


@app.get("/")
def index():
    """Serve the frontend."""
    return app.send_static_file("index.html")


@app.get("/api/readings")
def api_readings():
    """
    Return readings as a list of {t, p, e} where:
      - t: timestamp in ms since epoch
      - p: power in watts
      - e: cumulative energy in kWh
    Query params:
      - start: ISO string or ms since epoch (optional)
      - end: ISO string or ms since epoch (optional)
    """
    start = parse_time_param(request.args.get("start"))
    end = parse_time_param(request.args.get("end"))
    data = get_readings(start=start, end=end)
    return jsonify(data)


@app.get("/api/latest_reading")
def api_latest_reading():
    """Return the last reading."""
    return jsonify(latest_energy_reading())


@app.get("/api/stats")
def api_stats():
    """
    Compute stats between [start, end].
    Query params:
      - start: ISO string or ms since epoch (required)
      - end: ISO string or ms since epoch (required)
    """
    start = parse_time_param(request.args.get("start"))
    end = parse_time_param(request.args.get("end"))
    if start is None or end is None:
        return jsonify({"error": "start and end are required"}), 400
    if end < start:
        start, end = end, start
    stats = get_stats(start=start, end=end)
    return jsonify(
        {
            "start": int(start.timestamp() * 1000),
            "end": int(end.timestamp() * 1000),
            "stats": stats,
        }
    )


def start_threads():
    """Start the MQTT and schedule threads."""
    mqtt_thread = threading.Thread(target=mqtt_loop)
    schedule_thread = threading.Thread(target=schedule_loop)
    mqtt_thread.start()
    schedule_thread.start()
    # dont join the threads (blocks main thread which flask runs on)
    logger.info("Initilizaed threads for MQTT and schedule")


@app.get("/status")
def status():
    return {
        "status": "ok",
        "mqtt_connected": get_mqtt_client().is_connected(),
        "topic": TOPIC,
        "tasmota_url": TASMOTA_UI_URL,
        "flask_url": f"http://{SERVER_URL}:{FLASK_PORT}",
        "mqtt_server": f"{SERVER_URL}:{MQTT_PORT}",
        "scheduled_jobs": get_scheduled_jobs(),
        "last_reading": latest_energy_reading(),
        "num_readings_last_hour": num_energy_readings_last_hour(),
        "num_total_readings": num_total_energy_readings(),
    }


if __name__ == "__main__":
    start_threads()
    logger.info(f"Running on http://0.0.0.0:{FLASK_PORT}")
    logger.info(f"Running on : {SERVER_URL}:{FLASK_PORT}")
    logger.info(f"Status: {json.dumps(status(), indent=2)}")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
