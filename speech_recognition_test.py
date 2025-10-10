import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    print("Adjusting for ambient noise, please wait...")
    r.adjust_for_ambient_noise(source, duration=2)  # longer duration helps with slow speech
    
    print("Talk now...")
    # timeout=None waits indefinitely for someone to start talking
    # phrase_time_limit=None allows long sentences to be recorded
    audio_text = r.listen(source, timeout=None, phrase_time_limit=None)
    print("Recording finished.")

# Save audio to file to verify capture
with open("test_audio.wav", "wb") as f:
    f.write(audio_text.get_wav_data())

print("Audio saved as test_audio.wav")

import subprocess
import sys

from vosk import Model, KaldiRecognizer, SetLogLevel

SAMPLE_RATE = 16000

SetLogLevel(0)

model = Model(lang="en-us")
rec = KaldiRecognizer(model, SAMPLE_RATE)

with subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i",
                            sys.argv[1],
                            "-ar", str(SAMPLE_RATE) , "-ac", "1", "-f", "s16le", "-"],
                            stdout=subprocess.PIPE) as process:

    while True:
        data = process.stdout.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            print(rec.Result())
        else:
            print(rec.PartialResult())

    print(rec.FinalResult())