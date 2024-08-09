import asyncio
import websockets
import sounddevice as sd
import numpy as np
import json

async def send_audio(sender_id, receiver_id):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        while True:
            audio_data = sd.rec(1024, samplerate=44100, channels=1, dtype=np.int16)
            sd.wait()
            message = {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "audio_data": audio_data.tobytes()
            }
            await websocket.send(json.dumps(message))

sender_id = "sender_1"  # ID unik pengirim
receiver_id = "receiver_1"  # ID unik penerima
asyncio.get_event_loop().run_until_complete(send_audio(sender_id, receiver_id))
