import os
import struct
import subprocess
import time
import webbrowser
import sqlite3
import eel
import pvporcupine
import pyaudio
import pyautogui
import pywhatkit as kit
import pygame
import openai

from shlex import quote
from hugchat import hugchat

from backend.command import speak
from backend.config import ASSISTANT_NAME
from backend.helper import extract_yt_term, remove_words

# Initialize DB connection
conn = sqlite3.connect("jarvis.db")
cursor = conn.cursor()

# Initialize pygame mixer
pygame.mixer.init()

# Get BASE_DIR dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@eel.expose
def play_assistant_sound():
    try:
        sound_file = os.path.join(BASE_DIR, "frontend", "assets", "audio", "start_sound.mp3")
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"[ERROR] Sound file not played: {e}")
        speak("Assistant sound file not found or failed to play.")

def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "").replace("open", "").lower().strip()
    if not query:
        return

    try:
        cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (query,))
        results = cursor.fetchall()

        if results:
            speak("Opening " + query)
            os.startfile(results[0][0])
        else:
            cursor.execute('SELECT url FROM web_command WHERE name IN (?)', (query,))
            results = cursor.fetchall()
            if results:
                speak("Opening " + query)
                webbrowser.open(results[0][0])
            else:
                speak("Opening " + query)
                try:
                    os.system('start ' + query)
                except:
                    speak("Not found")
    except Exception as e:
        print(f"[ERROR] openCommand: {e}")
        speak("Something went wrong")

def PlayYoutube(query):
    search_term = extract_yt_term(query)
    speak("Playing " + search_term + " on YouTube")
    kit.playonyt(search_term)

def hotword():
    porcupine = None
    paud = None
    audio_stream = None
    try:
        porcupine = pvporcupine.create(
            access_key="GiHUH73YuKr8NZ5Zo88p/xE11meUMKLZGkJJ+R9kGlq1aB8o4hM2yQ==",
            keywords=["jarvis", "alexa"]
        )
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)

            if keyword_index >= 0:
                print("Hotword detected")
                pyautogui.keyDown("win")
                pyautogui.press("j")
                time.sleep(2)
                pyautogui.keyUp("win")

    except Exception as e:
        print(f"[ERROR] hotword detection: {e}")
    finally:
        if porcupine: porcupine.delete()
        if audio_stream: audio_stream.close()
        if paud: paud.terminate()


def findContact(query):
    try:
        query = remove_words(query, [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'whatsapp', 'video'])
        query = query.strip().lower()
        cursor.execute("SELECT Phone FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()

        if not results:
            speak('Contact not found.')
            return 0, 0

        phone = str(results[0][0])
        if not phone.startswith('+91'):
            phone = '+91' + phone

        return phone, query
    except Exception as e:
        print(f"[ERROR] findContact: {e}")
        speak('Error finding contact.')
        return 0, 0

def whatsApp(phone, message, flag, name):
    if flag == 'message':
        target_tab = 12
        jarvis_message = f"Message sent successfully to {name}"
    elif flag == 'call':
        target_tab = 7
        message = ''
        jarvis_message = f"Calling {name}"
    else:
        target_tab = 6
        message = ''
        jarvis_message = f"Starting video call with {name}"

    encoded_msg = quote(message)
    whatsapp_url = f"whatsapp://send?phone={phone}&text={encoded_msg}"
    command = f'start "" "{whatsapp_url}"'

    try:
        subprocess.run(command, shell=True)
        time.sleep(5)
        subprocess.run(command, shell=True)
        pyautogui.hotkey('ctrl', 'f')
        for _ in range(1, target_tab):
            pyautogui.hotkey('tab')
        pyautogui.hotkey('enter')
        speak(jarvis_message)
    except Exception as e:
        print(f"[ERROR] WhatsApp automation failed: {e}")
        speak("Failed to complete the WhatsApp task.")

# Set your OpenAI API Key
openai.api_key = "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"

def chatBot(query):
    try:
        user_input = query.strip().lower()
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant named Jarvis."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=150
        )

        reply = response["choices"][0]["message"]["content"].strip()
        print(f"[JarvisAI] {reply}")
        speak(reply)
        return reply

    except openai.error.AuthenticationError:
        error_msg = "Invalid OpenAI API key. Please check your configuration."
        print(f"[ERROR] {error_msg}")
        speak("API key is not valid.")
        return error_msg

    except openai.error.APIConnectionError:
        error_msg = "Network error connecting to OpenAI. Please check your internet connection."
        print(f"[ERROR] {error_msg}")
        speak("There seems to be a connection problem.")
        return error_msg

    except Exception as e:
        print(f"[ERROR] OpenAI response failed: {e}")
        speak("Sorry, I couldn't get a response from the AI model.")
        return "Jarvis is currently facing a technical issue."
