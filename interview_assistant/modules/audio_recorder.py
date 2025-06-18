import sounddevice as sd
import numpy as np
import wave
import queue
import threading
from config.settings import Settings

class AudioRecorder:
    def __init__(self):
        self.settings = Settings()
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.audio_queue = queue.Queue()
        
    def find_blackhole_device(self):
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if self.settings.BLACKHOLE_DEVICE in device['name']:
                return i
        raise ValueError("BlackHole device not found")

    def start_recording(self):
        device_id = self.find_blackhole_device()
        self.frames = []
        self.is_recording = True
        
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.audio_queue.put(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.settings.SAMPLE_RATE,
            channels=self.settings.CHANNELS,
            dtype=self.settings.DTYPE,
            callback=callback,
            device=device_id,
            blocksize=self.settings.CHUNK
        )
        self.stream.start()
        threading.Thread(target=self.process_audio, daemon=True).start()

    def process_audio(self):
        while self.is_recording or not self.audio_queue.empty():
            try:
                self.frames.append(self.audio_queue.get(timeout=0.1))
            except queue.Empty:
                continue

    def stop_recording(self, filename="interviewer.wav"):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        if self.frames:
            audio_data = np.concatenate(self.frames)
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.settings.CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(self.settings.SAMPLE_RATE)
                wf.writeframes(audio_data.tobytes())
        return filename