from gtts import gTTS
import os
import uuid


class TTSService:
    def __init__(self, output_dir="temp"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, text, lang="en"):

        try:
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(self.output_dir, filename)
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filepath)
            return filepath
        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    def cleanup(self, filepath):

        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Cleanup Error: {e}")
