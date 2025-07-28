import asyncio
import os
import json
from datetime import datetime
from aiocoap import Context, Message, Code
from aiocoap import resource
from shared.json_utils import load_json, save_json

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")
EVENT_FILE = os.path.join(DATA_FOLDER, "events-coap.json")
LED_FILE = os.path.join(DATA_FOLDER, "led_state.json")

os.makedirs(DATA_FOLDER, exist_ok=True)

class EventResource(resource.Resource):
    async def render_post(self, request):
        try:
            payload = json.loads(request.payload.decode())
            log = load_json(EVENT_FILE, [])
            log.append({
                "uuid": payload.get("uuid"),
                "event": payload.get("event"),
                "timestamp": payload.get("timestamp", int(datetime.utcnow().timestamp())),
                "iso": datetime.utcnow().isoformat()
            })
            save_json(EVENT_FILE, log)
            return Message(code=Code.CREATED, payload=b"Event stored")
        except Exception as e:
            return Message(code=Code.BAD_REQUEST, payload=str(e).encode())

class LEDResource(resource.Resource):
    async def render_post(self, request):
        try:
            payload = json.loads(request.payload.decode())
            state = payload.get("state", "off")
            save_json(LED_FILE, {"state": state})
            return Message(code=Code.CHANGED, payload=b"LED state updated")
        except Exception as e:
            return Message(code=Code.BAD_REQUEST, payload=str(e).encode())

async def main():
    if not os.path.exists(EVENT_FILE):
        save_json(EVENT_FILE, [])
    if not os.path.exists(LED_FILE):
        save_json(LED_FILE, {"state": "off"})

    root = resource.Site()
    root.add_resource(['event'], EventResource())
    root.add_resource(['led'], LEDResource())

    context = await Context.create_server_context(root, bind=("192.168.43.187", 5683))
    print("Serveur CoAP actif sur coap://192.168.43.187:5683/{event,led}")
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
