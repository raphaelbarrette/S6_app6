import json
from fastapi import FastAPI, HTTPException
import paho.mqtt.publish as publish
import os

app = FastAPI()

MQTT_BROKER_IP = "172.16.11.117"  # IP du broker MQTT (ex: Mosquitto)
MQTT_BROKER_PORT = 1883

MQTT_TOPIC_LED = "geoforce/led"
MQTT_TOPIC_EVENT = "geoforce/events"

DATA_FOLDER = "data"
EVENT_FILE = os.path.join(DATA_FOLDER, "events.json")
LED_FILE = os.path.join(DATA_FOLDER, "led_state.json")

def mqtt_post(topic, payload):
    publish.single(
        topic,
        payload=payload,
        hostname=MQTT_BROKER_IP,
        port=MQTT_BROKER_PORT
    )

def load_json(file, default):
    if not os.path.exists(file):
        return default
    if os.path.getsize(file) == 0:
        return default
    with open(file, 'r') as f:
        return json.load(f)

@app.get("/led")
async def get_led():
    try:
        led_state = load_json(LED_FILE, {"state": "off"})
        return led_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events")
async def get_events():
    try:
        events = load_json(EVENT_FILE, [])
        return events[-10:]  # Retourne les 10 derniers événements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/led")
async def set_led(state: dict):
    try:
        payload = json.dumps({"state": state.get("state", "off")})
        mqtt_post(MQTT_TOPIC_LED, payload)
        return {"message": "LED state published via MQTT"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/event")
async def post_event(event: dict):
    try:
        payload = json.dumps(event)
        mqtt_post(MQTT_TOPIC_EVENT, payload)
        return {"message": "Event published via MQTT"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))