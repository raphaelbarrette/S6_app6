import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt
from shared.json_utils import load_json, save_json

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")
EVENT_FILE = os.path.join(DATA_FOLDER, "events-mqtt.json")
LED_FILE = os.path.join(DATA_FOLDER, "led_state.json")

os.makedirs(DATA_FOLDER, exist_ok=True)

def on_connect(client, userdata, flags, rc):
    print("Connecté au broker MQTT avec code:", rc)
    client.subscribe("geoforce/events")
    client.subscribe("geoforce/led")

def on_message(client, userdata, msg):
    print(f"Message reçu sur [{msg.topic}]: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())

        if msg.topic == "geoforce/events":
            log = load_json(EVENT_FILE, [])
            log.append({
                "uuid": payload.get("uuid"),
                "event": payload.get("event"),
                "iso": datetime.utcnow().isoformat()
            })
            save_json(EVENT_FILE, log)

        elif msg.topic == "geoforce/led":
            state = payload.get("state", "off")
            save_json(LED_FILE, {"state": state})

    except Exception as e:
        print("Erreur de traitement:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.43.187", 1883)
client.loop_forever()
