import asyncio
import websockets
import json

clients = {}

async def register_client(websocket, client_id):
    """Add a new client to the clients list."""
    clients[client_id] = websocket
    print(f"Client {client_id} added to clients list")

async def unregister_client(websocket):
    """Remove a client from the clients list."""
    for client_id, ws in list(clients.items()):
        if ws == websocket:
            del clients[client_id]
            print(f"Client {client_id} disconnected and removed from clients list")
            break

async def handle_client(websocket, path):
    try:
        client_id = None
        print("Client connected")

        async for message in websocket:
            if isinstance(message, str):
                # Handle JSON message
                data = json.loads(message)
                sender_id = data.get("client_id")
                text = data.get("text")
                
                print(f"Received message from {sender_id}: {text}")

                if sender_id:
                    await register_client(websocket, sender_id)

                if text and sender_id:
                    # Forward the message to all clients except the sender
                    for cid, ws in clients.items():
                        if cid != sender_id:
                            await ws.send(message)
                            print(f"Forwarded message to {cid}: {text}")

    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
        await unregister_client(websocket)
    except Exception as e:
        print(f"Error: {e}")
        await unregister_client(websocket)

async def main():
    print("Server started, waiting for connections...")
    server = await websockets.serve(handle_client, "localhost", 8765)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
