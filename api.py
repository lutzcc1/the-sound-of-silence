from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from add_pauses import parse_script, generate_audio_file_from_chunks
import io

app = FastAPI(title="The-Sound-of-Silence")

@app.get("/generate")
def generate_audio():
  chunks = parse_script("Inhala profundo. [PAUSE:4s] Exhala lento… [PAUSE:6s] Buen trabajo.")
  audio = generate_audio_file_from_chunks(chunks)

  buf = io.BytesIO()
  audio.export(buf, format="ogg", codec="libopus") # this line encodes the raw PCM into a compressed format
  del audio # delete raw PCM to release memory
  buf.seek(0) # rewind buffer

  headers = {
    "Content-Disposition": "attachment; filename=meditacion.opus"
  }

  return StreamingResponse(buf, media_type="audio/opus", headers=headers)
