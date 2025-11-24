import json
import logging
import sys

import paho.mqtt.client as mqtt

from database import init_db
from database import save_energy_reading
from values import MQTT_PORT
from values import SERVER_URL
from values import TOPIC

logger = logging.getLogger(__name__)


def get_mqtt_client():
    """Get the MQTT client."""
    return mqtt.Client(protocol=mqtt.MQTTv5, userdata=None, transport="tcp")


def on_connect(client, userdata, flags, reason_code, properties):
    """Callback for when the MQTT client connects."""
    if reason_code.is_failure:
        logger.error(f"[connect] failed: {reason_code}")
        return
    logger.info("[connect] connected OK")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    """Callback for when the MQTT client receives a message."""
    try:
        payload = msg.payload.decode()
        # handle basic status messages
        if payload in ["Online", "Offline"]:
            logger.debug(f"[msg] {msg.topic}: {payload}")
            return
        data = json.loads(payload)
        logger.debug(f"[msg] {msg.topic}: {data}")
    except json.decoder.JSONDecodeError:
        logger.exception(f"[msg] {msg.topic}: {msg.payload}")
        return

    if "MT681" in data:
        save_energy_reading(tasmota_payload=data)


def on_disconnect(client, userdata, reason_code, properties):
    """Callback for when the MQTT client disconnects."""
    logger.info(f"[disconnect] code={reason_code}")


def mqtt_loop():
    """Loop the MQTT client."""
    init_db()
    if sys.platform == "darwin":
        logger.info("Using macOS, skipping MQTT loop")
        return
    mqtt_client = get_mqtt_client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    logger.info(f"Connecting to {SERVER_URL}:{MQTT_PORT} ...")
    mqtt_client.connect(SERVER_URL, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()
