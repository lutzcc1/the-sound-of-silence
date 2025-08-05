import re
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs
import io

PAUSE_SECONDS_RE = re.compile(r"\[PAUSE:(\d+)s\]", flags=re.IGNORECASE)
PAUSE_TAGS_RE = re.compile(r"\[PAUSE:\d+s\]", flags=re.IGNORECASE)

def parse_script(script):
    """
    Returns [(spoken_text, pause_after_seconds), ...]
    where the *final* chunk always has pause 0.
    """
    # Grab all pauses as integers.
    pauses = [int(sec) for sec in PAUSE_SECONDS_RE.findall(script)]
    # Split into chunks & srip whitespace.
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
  client = ElevenLabs(api_key='sk_dbee9c4ca13c8f5767bde8fb07e306920ca4d37397234485')

  return client.text_to_speech.convert(
      voice_id="JBFqnCBsd6RMkjVDRZzb",
      output_format="opus_48000_32",
      text=text,
      model_id="eleven_multilingual_v2",
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

# ── Quick sanity checks ────────────────────────────────────────────────────────
if __name__ == "__main__":
    s1 = "Inhala profundo. [PAUSE:4s] Exhala lento… [PAUSE:6s] Buen trabajo."
    print(parse_script(s1))
    # [('Inhala profundo.', 4), ('Exhala lento…', 6), ('Buen trabajo.', 0)]

    s2 = "Relájate. [PAUSE:10s][PAUSE:2s] Suelta."  # consecutive pauses
    try:
        parse_script(s2)
    except ValueError as e:
        print("Caught:", e)

    s3 = "Final tag issue. [PAUSE:3s]"  # trailing pause
    try:
        parse_script(s3)
    except ValueError as e:
        print("Caught:", e)

    test_script = "Inhala profundo. [PAUSE:4s] Exhala lento… [PAUSE:6s] Buen trabajo."
    chunks = parse_script(test_script)
    audio = generate_audio_file_from_chunks(chunks)
    audio.export('combined.mp3', format="mp3")
