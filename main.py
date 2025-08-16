import io
import os
import tempfile

from add_pauses import parse_script, generate_audio_file_from_chunks
from audio_mixer import add_background_music
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from pydub import AudioSegment

load_dotenv()

APP_API_KEY = os.environ["APP_API_KEY"]
MUSIC_PATH = os.environ.get("MUSIC_PATH", "music.wav")

app = FastAPI(title="The-Sound-of-Silence")

class Script(BaseModel):
  script: str

@app.post("/generate")
def generate_audio(request: Script, x_api_key: Optional[str] = Header(None)):
  if x_api_key != APP_API_KEY:
    raise HTTPException(status_code=401, detail="Unauthorized")

  chunks = parse_script(request.script)
  narration_audio = generate_audio_file_from_chunks(chunks)

  # Export narration to a temp WAV so the mixer can align/sample-rate properly
  with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as narr_tmp:
    narration_path = narr_tmp.name
  narration_audio.export(narration_path, format="wav")

  # Mix with background music into another temp WAV
  with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as mixed_tmp:
    mixed_path = add_background_music(
      narration_path=narration_path,
      music_path=MUSIC_PATH,
      out_path=mixed_tmp.name,
    )

  # Load the mixed audio and stream as Opus
  final_audio = AudioSegment.from_file(mixed_path)

  buf = io.BytesIO()
  final_audio.export(buf, format="ogg", codec="libopus") # encode to Opus
  del final_audio # delete raw PCM to release memory
  buf.seek(0) # rewind buffer

  # Clean up temporary files
  try:
    os.unlink(narration_path)
  finally:
    try:
      os.unlink(mixed_path)
    except Exception:
      pass

  headers = {
    "Content-Disposition": "attachment; filename=meditacion.opus"
  }

  return StreamingResponse(buf, media_type="audio/opus", headers=headers)

@app.get("/health", tags=["health"])
def health_check():
  return JSONResponse(status_code=200, content={"status": "ok"})
