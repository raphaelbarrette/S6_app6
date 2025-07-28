import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import paho.mqtt.publish as mqtt_publish
from aiocoap import Context, Message, Code
import asyncio
from shared.json_utils import load_json

app = FastAPI()

# Pour permettre les appels frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
DATA_FOLDER = "data"
LED_FILE = os.path.join(DATA_FOLDER, "led_state.json")
# Déterminer le mode : mqtt ou coap
MODE = os.environ.get("GEOFORCE_MODE", "mqtt")
COAP_SERVER_IP = "192.168.43.187"
MQTT_BROKER_IP = "192.168.43.187"
MQTT_TOPIC_EVENT = "geoforce/events"
MQTT_TOPIC_LED = "geoforce/led"

# ---------- Fonctions d'envoi ----------

def mqtt_post(topic, payload: dict):
    mqtt_publish.single(
        topic,
        payload=json.dumps(payload),
        hostname=MQTT_BROKER_IP
    )

async def coap_post(path: str, payload: dict):
    context = await Context.create_client_context()
    request = Message(
        code=Code.POST,
        uri=f"coap://{COAP_SERVER_IP}/{path}",
        payload=json.dumps(payload).encode()
    )
    await context.request(request).response

# ---------- Endpoints ----------

@app.post("/event")
async def post_event(event: dict):
    try:
        if MODE == "mqtt":
            mqtt_post(MQTT_TOPIC_EVENT, event)
        elif MODE == "coap":
            await coap_post("event", event)
        return {"message": "Événement relayé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/led")
async def post_led(state: dict):
    try:
        if MODE == "mqtt":
            mqtt_post(MQTT_TOPIC_LED, state)
        elif MODE == "coap":
            await coap_post("led", state)
        return {"message": "Commande LED relayée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/led")
async def get_led():
    try:
        led_state = load_json(LED_FILE, {"state": "off"})
        return led_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
