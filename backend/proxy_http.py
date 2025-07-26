import asyncio
from fastapi import FastAPI, HTTPException
from aiocoap import Context, Message, Code
import json

app = FastAPI()

COAP_SERVER_IP = "10.0.0.115"

async def coap_get(path):
    context = await Context.create_client_context()
    request = Message(code=Code.GET, uri=f"coap://{COAP_SERVER_IP}/{path}")
    response = await context.request(request).response
    return response.payload.decode()

async def coap_post(path, payload):
    context = await Context.create_client_context()
    request = Message(code=Code.POST, uri=f"coap://{COAP_SERVER_IP}/{path}", payload=json.dumps(payload).encode())
    response = await context.request(request).response

    print("Raw CoAP Response:", response.payload)

    if not response.payload:
        return "OK"
    return response.payload.decode()

@app.get("/led")
async def get_led():
    try:
        result = await coap_get("led")
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/led")
async def set_led(state: dict):
    try:
        result = await coap_post("led", state)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/event")
async def post_event(event: dict):
    try:
        await coap_post("event", event)
        return {"message": "Event transmitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events")
async def get_events():
    try:
        with open("data/events.json", "r") as f:
            events = json.load(f)
        return events[-10:]  # Renvoie les 10 derniers événements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))