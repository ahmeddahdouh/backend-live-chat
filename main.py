import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS : autoriser tout (développement local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structure client : { "websocket": WebSocket, "username": str }
clients = []

@app.get("/")
def read_root():
    return {"message": "Hello, World! FastAPI server is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "clients_connected": len(clients)}

@app.websocket("/ws/chat/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    clients.append({"websocket": websocket, "username": username})
    print(f"{username} connecté. Clients: {len(clients)}")

    # Envoyer le nombre d'utilisateurs en ligne à tous
    await broadcast_user_count()

    try:
        while True:
            data = await websocket.receive_text()
            print(f"{username} a envoyé : {data}")

            # Créer un message JSON structuré
            message = {
                "type": "message",
                "text": data,
                "sender": username
            }

            await broadcast_message(message)

    except WebSocketDisconnect:
        print(f"{username} s'est déconnecté")
        clients[:] = [c for c in clients if c["websocket"] != websocket]
        await broadcast_user_count()


async def broadcast_message(message: dict):
    disconnected = []
    for client in clients:
        try:
            await client["websocket"].send_text(json.dumps(message))
        except Exception as e:
            print(f"Erreur d'envoi à {client['username']}: {e}")
            disconnected.append(client)

    for client in disconnected:
        clients.remove(client)


async def broadcast_user_count():
    message = {
        "type": "user_count",
        "count": len(clients)
    }
    await broadcast_message(message)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
