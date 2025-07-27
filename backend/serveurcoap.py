import asyncio
from aiocoap import Context, Message, Code
from aiocoap import resource
import json
import os
from datetime import datetime

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
EVENT_FILE = os.path.join(DATA_FOLDER, 'events.json')
LED_FILE = os.path.join(DATA_FOLDER, 'led_state.json')

# ----- Utils -----
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

# ----- Ressources CoAP -----
class EventResource(resource.Resource):
    async def render_post(self, request):
        try:
            print("Payload brut reçu (CoAP):", request.payload)
            payload = json.loads(request.payload.decode('utf-8'))
            print(f"payload apres json {payload}")
            uuid = payload.get("uuid")
            event = payload.get("event")
            timestamp = payload.get("timestamp", int(datetime.utcnow().timestamp()))

            print(f"on cest rendu la i guess")
            log = load_json(EVENT_FILE, [])
            log.append({
                "uuid": uuid,
                "event": event,
                "timestamp": timestamp,
                "iso": datetime.utcnow().isoformat()
            })
            print(f"log is {log}")
            save_json(EVENT_FILE, log)

            return Message(code=Code.CREATED, payload=b"Event stored")
        except Exception as e:
            print(f"Exception dans render_post: {e}")
            return Message(code=Code.BAD_REQUEST, payload=str(e).encode())

class LEDResource(resource.Resource):
    async def render_get(self, request):
        state = load_json(LED_FILE, {"state": "off"})
        return Message(payload=json.dumps(state).encode('utf-8'))

    async def render_post(self, request):
        try:
            payload = json.loads(request.payload.decode('utf-8'))
            state = payload.get("state", "off")
            save_json(LED_FILE, {"state": state})
            return Message(code=Code.CHANGED, payload=b"LED state updated")
        except Exception as e:
            return Message(code=Code.BAD_REQUEST, payload=str(e).encode())

async def main():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    # Initialiser les fichiers s'ils n'existent pas
    if not os.path.exists(EVENT_FILE):
        save_json(EVENT_FILE, [])
    if not os.path.exists(LED_FILE):
        save_json(LED_FILE, {"state": "off"})

    root = resource.Site()
    root.add_resource(['event'], EventResource())
    root.add_resource(['led'], LEDResource())

    context = await Context.create_server_context(root, bind=('192.168.68.65', 5683))
    print("Serveur CoAP actif sur coap://0.0.0.0:{event,led}")

    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())