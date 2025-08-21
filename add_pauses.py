import io
import os
import re

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from pydub import AudioSegment

load_dotenv()

ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
PAUSE_SECONDS_RE = re.compile(r"\[PAUSE:(\d+)s\]", flags=re.IGNORECASE)
PAUSE_TAGS_RE = re.compile(r"\[PAUSE:\d+s\]", flags=re.IGNORECASE)
VOICE_ID = os.environ["VOICE_ID"]
MODEL_ID = os.environ["MODEL_ID"]

ElevenLabsClient = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def parse_script(script):
    """
    Returns [(spoken_text, pause_after_seconds), ...]
    where the *final* chunk always has pause 0.
    """
    # Grab all pauses as integers.
    pauses = [int(sec) for sec in PAUSE_SECONDS_RE.findall(script)]
    # Split into chunks & strip whitespace.
    chunks = [c.strip() for c in PAUSE_TAGS_RE.split(script) if c.strip()]

    # We expect exactly one more chunk than pauses. Final chunk has no pause
    if len(chunks) != len(pauses) + 1:
        raise ValueError(
            "The script ends with a [PAUSE] tag or has consecutive pauses."
        )

    result = []
    for i, chunk in enumerate(chunks):
        pause_after = pauses[i] if i < len(pauses) else 0
        result.append((chunk, pause_after))

    return result

def fetch_tts(text):
  return ElevenLabsClient.text_to_speech.convert(
      voice_id=VOICE_ID,
      output_format="opus_48000_32",
      text=text,
      model_id=MODEL_ID,
      voice_settings=VoiceSettings(speed=0.90, stability=0.70, similarity_boost=0.40, use_speaker_boost=True)
  )

def generate_audio_segment(text):
  # ElevenLabs returns an audio generator
  generator = fetch_tts(text)

  # get the full binary data from generator
  audio_bytes = b"".join(generator)

  # according to AudioSegment docs it is possible to build a segment from raw audio data
  # but I wasn't able to make it work, hence the IO operation
  return AudioSegment.from_file(io.BytesIO(audio_bytes), format="ogg")

# Example of 'chunks': [('Inhala profundo.', 4), ('Exhala lento…', 6), ('Buen trabajo.', 0)]
def generate_audio_file_from_chunks(chunks):
  combined_audio = AudioSegment.empty()

  for chunk in chunks:
    audio_segment = generate_audio_segment(chunk[0])
    pause_segment = AudioSegment.silent(duration=chunk[1] * 1000)

    combined_audio += audio_segment + pause_segment

  return combined_audio
