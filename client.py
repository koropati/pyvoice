import tkinter as tk
from tkinter import messagebox
import asyncio
import websockets
import json
import speech_recognition as sr
from gtts import gTTS
import io
from pygame import mixer
from threading import Thread

class VoiceClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Client")
        self.websocket = None
        self.is_recording = False

        # Create GUI elements
        self.room_id_label = tk.Label(root, text="Room ID")
        self.room_id_label.pack()
        self.room_id_entry = tk.Entry(root)
        self.room_id_entry.pack()

        self.client_id_label = tk.Label(root, text="Client ID")
        self.client_id_label.pack()
        self.client_id_entry = tk.Entry(root)
        self.client_id_entry.pack()

        self.connect_button = tk.Button(root, text="Connect", command=self.start_connect)
        self.connect_button.pack()

        self.disconnect_button = tk.Button(root, text="Disconnect", state=tk.DISABLED, command=self.disconnect_websocket)
        self.disconnect_button.pack()

        self.start_button = tk.Button(root, text="Start Recording", state=tk.DISABLED, command=self.start_recording)
        self.start_button.pack()

        self.stop_button = tk.Button(root, text="Stop Recording", state=tk.DISABLED, command=self.stop_recording)
        self.stop_button.pack()

        self.status_label = tk.Label(root, text="Status: Disconnected")
        self.status_label.pack()

        # Initialize pygame mixer for playing audio
        mixer.init()

        # Create and run the asyncio event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.loop_thread = Thread(target=self.run_event_loop, daemon=True)
        self.loop_thread.start()

    def run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start_connect(self):
        # Schedule the coroutine to run in the asyncio event loop
        asyncio.run_coroutine_threadsafe(self.connect_websocket(), self.loop)

    async def connect_websocket(self):
        room_id = self.room_id_entry.get()
        client_id = self.client_id_entry.get()

        if not room_id or not client_id:
            messagebox.showerror("Error", "Please enter both room ID and client ID")
            return

        uri = 'ws://localhost:8765'
        self.websocket = await websockets.connect(uri)

        await self.websocket.send(json.dumps({
            'type': 'register',
            'room_id': room_id,
            'client_id': client_id
        }))

        self.status_label.config(text="Status: Connected")
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)

        # Start receiving messages
        asyncio.create_task(self.receive_messages())

    async def disconnect_websocket(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        self.status_label.config(text="Status: Disconnected")
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

    async def receive_messages(self):
        while True:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)

                if 'text' in data:
                    text = data['text']
                    self.play_text(text)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def play_text(self, text):
        tts = gTTS(text=text, lang='id')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        mixer.music.load(fp)
        mixer.music.play()
        print("Playing received text:", text)

    def start_recording(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_recording = True

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Start a thread to handle recording
        self.recording_thread = Thread(target=self.record_audio)
        self.recording_thread.start()

    def record_audio(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)

            while self.is_recording:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    transcript = self.recognizer.recognize_google(audio, language='id')
                    print("Recognized speech:", transcript)

                    if self.websocket:
                        asyncio.run_coroutine_threadsafe(self.websocket.send(json.dumps({
                            'type': 'text',
                            'room_id': self.room_id_entry.get(),
                            'client_id': self.client_id_entry.get(),
                            'text': transcript
                        })), self.loop)
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")

    def stop_recording(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_recording = False

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceClientApp(root)
    root.mainloop()
