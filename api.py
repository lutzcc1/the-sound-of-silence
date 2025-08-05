import io
import os

from add_pauses import parse_script, generate_audio_file_from_chunks
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

load_dotenv()

APP_API_KEY = os.environ["APP_API_KEY"]

app = FastAPI(title="The-Sound-of-Silence")

class Script(BaseModel):
  script: str

@app.post("/generate")
def generate_audio(request: Script, x_api_key: Optional[str] = Header(None)):
  if x_api_key != APP_API_KEY:
    raise HTTPException(status_code=401, detail="Unauthorized")

  chunks = parse_script(request.script)
  audio = generate_audio_file_from_chunks(chunks)

  buf = io.BytesIO()
  audio.export(buf, format="ogg", codec="libopus") # this line encodes the raw PCM into a compressed format
  del audio # delete raw PCM to release memory
  buf.seek(0) # rewind buffer

  headers = {
    "Content-Disposition": "attachment; filename=meditacion.opus"
  }

  return StreamingResponse(buf, media_type="audio/opus", headers=headers)
