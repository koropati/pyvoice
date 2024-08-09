import asyncio
import websockets
import json
import base64
import sounddevice as sd
import numpy as np

async def receive_audio(receiver_id):
    uri = "ws://localhost:8765"
    print(f"Connecting to WebSocket server at {uri} as receiver {receiver_id}...")

    async with websockets.connect(uri) as websocket:
        print(f"Connected to WebSocket server as receiver {receiver_id}")

        while True:
            try:
                message = await websocket.recv()
                print(f"Received raw message: {message}")
                
                data = json.loads(message)
                print(f"Decoded data: {data}")

                if 'audio_data' in data:
                    audio_data_base64 = data['audio_data']
                    print(f"Received audio data with length: {len(audio_data_base64)} characters")

                    # Convert audio data from base64 to bytes
                    audio_data_bytes = base64.b64decode(audio_data_base64)
                    
                    # Assuming the audio data is in 16-bit PCM format
                    audio_array = np.frombuffer(audio_data_bytes, dtype=np.int16)
                    
                    # Play the audio
                    sd.play(audio_array, samplerate=44100)
                    sd.wait()
                    print("Played received audio data")
                else:
                    print("No audio data found in the message")
            except Exception as e:
                print(f"Error receiving audio data: {e}")
                break


async def main(receiver_id):
    await receive_audio(receiver_id)

if __name__ == "__main__":
    receiver_id = "receiver_1"  # ID unik penerima
    asyncio.run(main(receiver_id))
