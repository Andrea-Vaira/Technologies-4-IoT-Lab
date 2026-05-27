import requests
import json
import time

URL = "http://localhost:8080/"

while True:
    try:
        response = requests.get(URL)
        if response.status_code == 200:
            print("\n--- STATO ATTUALE DEL CATALOGO ---")
            print(json.dumps(response.json(), indent=4))
        else:
            print(f"Errore del server: {response.status_code}")
    except Exception as e:
        print(f"Impossibile connettersi al server REST: {e}")
    
    time.sleep(10) # Controlla lo stato ogni 10 secondi