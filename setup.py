from setuptools import setup

APP = ['chatgpt_toggle_listener.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['numpy', 'sounddevice', 'wave', 'threading', 'tkinter', 'queue', 'textract', 'pyautogui', 'PIL', 'pynput', 'Quartz', 'openai', 'dotenv'],
    'iconfile': 'app_icon.icns',  # Optional: put a custom icon here if you want
    'plist': {
        'CFBundleName': 'Interview Assistant',
        'CFBundleDisplayName': 'Interview Assistant',
        'CFBundleIdentifier': 'com.yourcompany.interviewassistant',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

