import os
import eel
from backend.auth import recoganize
from backend.auth.recoganize import AuthenticateFace
from backend.feature import *
from backend.command import *
import openai
from backend.helper import speak  # Make sure you have speak() in helper.py
import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("AIzaSyBigSxWdnsZHI_WmgX8JLudASKYmDx8W1g")

# Your OpenAI API Key

def chatBot(query):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # You can use "gpt-4" if available
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": query}
            ]
        )
        reply = response['choices'][0]['message']['content']
        print(f"[GPT] {reply}")
        speak(reply)
        return reply
    except Exception as e:
        print(f"[ERROR] OpenAI API: {e}")
        speak("Sorry, I couldn't connect to ChatGPT.")
        return "Error"


def start():
    eel.init("frontend")

    play_assistant_sound()

    @eel.expose
    def init():
        try:
            print("[DEBUG] init() called from frontend")
            eel.hideLoader()
            speak("Welcome to Jarvis")
            speak("Ready for Face Authentication")

            flag = recoganize.AuthenticateFace()

            if flag == 1:
                speak("Face recognized successfully")
                eel.hideFaceAuth()
                eel.hideFaceAuthSuccess()
                speak("Welcome to Your Assistant")
                eel.hideStart()
                play_assistant_sound()
            else:
                speak("Face not recognized. Please try again")

            return {"status": "ok"}  # ✅ always return something valid
        except Exception as e:
            print(f"[ERROR] init() failed: {e}")
            return {"status": "error", "message": str(e)}  # ✅ avoid KeyError

    # ✅ Launch in Microsoft Edge browser
    os.system('start msedge.exe --app="http://127.0.0.1:8082/index.html"')

    # ✅ Start Eel webserver on port 8081
    eel.start("index.html", mode=None, host="localhost", port=8082, block=True)



# ✅ Run start() if script is executed directly
if __name__ == "__main__":
    start()
