import os
import asyncio
from pyngrok import ngrok, conf
import uvicorn
from main import app

async def main():
    """
    Fonction principale asynchrone qui orchestre le lancement du serveur et du tunnel.
    """
    # --- Configuration de Ngrok ---
    # NGROK_TOKEN = userdata.get('NGROK_TOKEN')
    if not NGROK_TOKEN:
        raise ValueError("La variable d'environnement NGROK_AUTH_TOKEN n'est pas définie.")
    conf.get_default().auth_token = NGROK_TOKEN

    # --- Lancement du serveur Uvicorn en arrière-plan ---
    config = uvicorn.Config(app, host="0.0.0.0", port=8502, log_level="info")
    server = uvicorn.Server(config)
    
    # On lance le serveur comme une tâche asyncio
    server_task = asyncio.create_task(server.serve())
    
    print("🚀 Serveur Uvicorn démarré en arrière-plan.")
    
    # Petite pause pour s'assurer que le serveur est bien démarré avant de lancer ngrok
    await asyncio.sleep(2)

    # --- Création du tunnel Ngrok ---
    public_url = ngrok.connect(8502, "http")
    print("="*60)
    print(f"✅ Service déployé et accessible publiquement à l'adresse : {public_url}")
    print(f"📚 Accédez à l'interface de test Swagger UI ici : {public_url}/docs")
    print("="*60)

    # On attend que la tâche du serveur se termine (ce qui n'arrivera que si on l'arrête)
    await server_task

if __name__ == "__main__":
    try:
        # On lance la boucle d'événements avec notre fonction main
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArrêt du service...")
        ngrok.disconnect_all() # On ferme proprement les tunnels ngrok
