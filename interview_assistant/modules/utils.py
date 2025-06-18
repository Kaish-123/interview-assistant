def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {str(e)}")
            return None
    return wrapper

import requests

def check_internet_connection():
    try:
        requests.get("https://api.openai.com", timeout=5)
        return True
    except:
        return False