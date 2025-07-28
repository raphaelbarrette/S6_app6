import subprocess
import argparse
import sys
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lance le système GeoForce")
    parser.add_argument("--mode", choices=["mqtt", "coap"], required=True, help="Mode d'exécution : mqtt ou coap")
    args = parser.parse_args()

    # Définit une variable d’environnement pour le mode
    os.environ["GEOFORCE_MODE"] = args.mode

    # Lance le relai (FastAPI)
    subprocess.Popen([sys.executable, "relay/main.py"])

    # Lance le backend de persistance (MQTT ou CoAP)
    if args.mode == "mqtt":
        subprocess.Popen([sys.executable, "mqtt/subscriber.py"])
    elif args.mode == "coap":
        subprocess.Popen([sys.executable, "coap/server.py"])

    subprocess.Popen([sys.executable, "app_backend/main.py"])
    print(f"Mode '{args.mode}' lancé. Relai HTTP et backend {args.mode.upper()} en cours d'exécution.")

    # Garder le processus principal en vie
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nArrêt manuel.")
