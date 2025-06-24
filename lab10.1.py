import json
import time
import webbrowser
import requests

import pyttsx3
import pyaudio
import vosk


class Speech:
    def __init__(self):
        self.tts = pyttsx3.init('sapi5')

    def set_voice(self, speaker=1):
        voices = self.tts.getProperty('voices')
        for count, voice in enumerate(voices):
            if speaker == count:
                return voice.id
        return voices[0].id

    def text2voice(self, speaker=1, text='Ready'):
        self.tts.setProperty('voice', self.set_voice(speaker))
        print(f'🎤 Assistant: {text}')
        self.tts.say(text)
        self.tts.runAndWait()


class Recognize:
    def __init__(self):
        model = vosk.Model('model')  
        self.record = vosk.KaldiRecognizer(model, 16000)
        self.stream_audio()

    def stream_audio(self):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=16000,
                              input=True,
                              frames_per_buffer=8000)

    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.record.AcceptWaveform(data):
                answer = json.loads(self.record.Result())
                if answer.get('text'):
                    yield answer['text']


class DictionaryAssistant:
    def __init__(self):
        self.speech = Speech()
        self.recognize = Recognize()
        self.current_word = None
        self.current_data = None

    def fetch_word(self, word):
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            self.current_word = word
            self.current_data = data
            self.speech.text2voice(speaker=1, text=f"I found the word {word}. You can ask for meaning, example, link, or save.")
        except Exception:
            self.speech.text2voice(speaker=1, text=f"Sorry, I could not find the word {word}. Try another.")

    def say_meaning(self):
        if not self.current_data:
            self.speech.text2voice(speaker=1, text="No word loaded. Say find followed by the word.")
            return
        try:
            meanings = self.current_data[0]['meanings']
            first_def = meanings[0]['definitions'][0]['definition']
            self.speech.text2voice(speaker=1, text=f"The meaning of {self.current_word} is: {first_def}")
        except Exception:
            self.speech.text2voice(speaker=1, text="Sorry, I couldn't get the meaning.")

    def say_example(self):
        if not self.current_data:
            self.speech.text2voice(speaker=1, text="No word loaded. Say find followed by the word.")
            return
        try:
            example = self.current_data[0]['meanings'][0]['definitions'][0].get('example')
            if example:
                self.speech.text2voice(speaker=1, text=f"Example: {example}")
            else:
                self.speech.text2voice(speaker=1, text="No example available for this word.")
        except Exception:
            self.speech.text2voice(speaker=1, text="Sorry, I couldn't get the example.")

    def open_link(self):
        if not self.current_word:
            self.speech.text2voice(speaker=1, text="No word loaded. Say find followed by the word.")
            return
        url = f"https://www.dictionary.com/browse/{self.current_word}"
        webbrowser.open(url)
        self.speech.text2voice(speaker=1, text=f"Opening the link for {self.current_word}.")

    def save_info(self):
        if not self.current_data or not self.current_word:
            self.speech.text2voice(speaker=1, text="No word loaded to save.")
            return
        try:
            meanings = self.current_data[0]['meanings']
            first_def = meanings[0]['definitions'][0]['definition']
            example = meanings[0]['definitions'][0].get('example', 'No example available.')
            filename = f"{self.current_word}_definition.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Word: {self.current_word}\nMeaning: {first_def}\nExample: {example}\n")
            self.speech.text2voice(speaker=1, text=f"Information about {self.current_word} saved to {filename}.")
        except Exception:
            self.speech.text2voice(speaker=1, text="Failed to save the information.")

    def run(self):
        self.speech.text2voice(speaker=1, text="Dictionary assistant is ready. Say 'find' followed by a word.")
        for phrase in self.recognize.listen():
            print(f'You said: {phrase}')

            if phrase.startswith("find "):
                word = phrase[5:].strip()
                if word:
                    self.fetch_word(word)
                else:
                    self.speech.text2voice(speaker=1, text="Please say the word after find.")
            elif phrase == "meaning":
                self.say_meaning()
            elif phrase == "example":
                self.say_example()
            elif phrase == "link":
                self.open_link()
            elif phrase == "save":
                self.save_info()
            elif phrase == "exit" or phrase == "quit":
                self.speech.text2voice(speaker=1, text="Goodbye!")
                break
            else:
                self.speech.text2voice(speaker=1, text="Command not recognized. Please say find, meaning, example, link, save, or exit.")


if __name__ == "__main__":
    assistant = DictionaryAssistant()
    assistant.run()
