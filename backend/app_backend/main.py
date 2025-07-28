import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Pour appels frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Détecte le mode actuel
MODE = os.environ.get("GEOFORCE_MODE", "mqtt")  # défaut : mqtt

# Chemins des fichiers
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")
EVENT_FILE_MQTT = os.path.join(DATA_FOLDER, "events-mqtt.json")
EVENT_FILE_COAP = os.path.join(DATA_FOLDER, "events-coap.json")

@app.get("/events")
def get_events():
    """
    Retourne les derniers événements selon le mode actuel (MQTT ou CoAP).
    """
    try:
        if MODE == "mqtt":
            filepath = EVENT_FILE_MQTT
        elif MODE == "coap":
            filepath = EVENT_FILE_COAP
        else:
            raise HTTPException(status_code=500, detail=f"Mode inconnu : {MODE}")

        if not os.path.exists(filepath):
            return []

        with open(filepath, "r") as f:
            data = json.load(f)
            return data[-10:]  # derniers événements

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print(f"App backend lancée en mode {MODE.upper()}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
