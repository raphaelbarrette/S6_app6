import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
EVENT_FILE = os.path.join(DATA_FOLDER, 'events.json')
LED_FILE = os.path.join(DATA_FOLDER, 'led_state.json')

def load_json(file, default):
    if not os.path.exists(file):
        return default
    if os.path.getsize(file) == 0:  # fichier vide
        return default
    with open(file, 'r') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def on_connect(client, userdata, flags, rc):
    print("Connecté au broker MQTT avec code:", rc)
    client.subscribe("geoforce/events")
    client.subscribe("geoforce/led")

def on_message(client, userdata, msg):
    print(f"Message reçu sur {msg.topic}: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())

        if msg.topic == "geoforce/events":
            log = load_json(EVENT_FILE, [])
            log.append({
                "uuid": payload.get("uuid"),
                "event": payload.get("event"),
                "timestamp": payload.get("timestamp", int(datetime.utcnow().timestamp())),
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

client.connect("192.168.68.65", 1883)
client.loop_forever()
