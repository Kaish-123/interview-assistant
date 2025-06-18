import os

class Settings:
    API_KEY = os.getenv("API_KEY")
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'
    CHUNK = 1024
    BLACKHOLE_DEVICE = "BlackHole"
    GPT_MODEL = "gpt-4-turbo"
    WHISPER_MODEL = "whisper-1"