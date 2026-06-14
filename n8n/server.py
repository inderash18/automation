import os
import uuid
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import functions from scripts
from scripts.generate_script import generate_script
from scripts.tts import text_to_speech
from scripts.video import build_video

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video-pipeline-server")

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Automated Video Generation API",
    description="FastAPI bridge for n8n to generate automated scripts, speech, and video composites.",
    version="1.0.0"
)

# Enable CORS for local testing/access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the assets folder to serve the generated audio and videos statically
os.makedirs("assets", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Request Models
class ScriptRequest(BaseModel):
    topic: str = Field(..., example="5 shocking facts about the oceans")
    style: str = Field("engaging, informative, fast-paced", example="engaging, mystery-style")
    duration: str = Field("60 seconds", example="30 seconds")
    output_path: str = Field("assets/script.txt", example="assets/script.txt")

class TTSRequest(BaseModel):
    text: str = Field(None, description="Direct text to convert. If empty, reads assets/script.txt")
    voice: str = Field("en-US-AvaNeural", description="Microsoft Edge TTS voice name")
    output_audio: str = Field("assets/voice.mp3")
    output_srt: str = Field("assets/voice.srt")

class VideoRequest(BaseModel):
    bg_path: str = Field("assets/bg.mp4", description="Path to background video (optional)")
    audio_path: str = Field("assets/voice.mp3")
    srt_path: str = Field("assets/voice.srt")
    output_path: str = Field("assets/final.mp4")
    width: int = Field(1080)
    height: int = Field(1920)
    font_size: int = Field(60)

class PipelineRequest(BaseModel):
    topic: str
    style: str = "engaging, informative, fast-paced"
    duration: str = "60 seconds"
    voice: str = "en-US-AvaNeural"
    bg_path: str = "assets/bg.mp4"
    font_size: int = 60
    background: bool = Field(False, description="Whether to run in the background as an async task")

# Simple memory store for background tasks
task_store = {}

def execute_pipeline(task_id: str, req: PipelineRequest):
    """Executes the full pipeline and updates the task store."""
    try:
        task_store[task_id] = {"status": "processing", "progress": "generating script"}
        logger.info(f"Task {task_id}: Generating script...")
        
        # 1. Script Generation
        script_text = generate_script(
            topic=req.topic,
            style=req.style,
            duration=req.duration,
            output_path="assets/script.txt"
        )
        
        # 2. TTS Generation
        task_store[task_id] = {"status": "processing", "progress": "generating text-to-speech"}
        logger.info(f"Task {task_id}: Converting text to speech...")
        
        import asyncio
        # edge-tts is async, so we run it in a new event loop or using the current runner
        asyncio.run(text_to_speech(
            text=script_text,
            voice=req.voice,
            output_audio="assets/voice.mp3",
            output_srt="assets/voice.srt"
        ))
        
        # 3. Video composition
        task_store[task_id] = {"status": "processing", "progress": "compositing video"}
        logger.info(f"Task {task_id}: Building video composition...")
        
        build_video(
            bg_path=req.bg_path,
            audio_path="assets/voice.mp3",
            srt_path="assets/voice.srt",
            output_path="assets/final.mp4",
            width=1080,
            height=1920,
            font_size=req.font_size
        )
        
        task_store[task_id] = {
            "status": "completed",
            "progress": "done",
            "assets": {
                "script": "/assets/script.txt",
                "audio": "/assets/voice.mp3",
                "srt": "/assets/voice.srt",
                "video": "/assets/final.mp4"
            }
        }
        logger.info(f"Task {task_id}: Completed successfully.")
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        task_store[task_id] = {
            "status": "failed",
            "error": str(e)
        }

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Automated Video Pipeline Server is running.",
        "endpoints": {
            "/generate-script": "POST",
            "/generate-audio": "POST",
            "/generate-video": "POST",
            "/run-pipeline": "POST",
            "/task/{task_id}": "GET",
            "/assets/{filename}": "GET"
        }
    }

@app.post("/generate-script")
def api_generate_script(req: ScriptRequest):
    try:
        script_text = generate_script(
            topic=req.topic,
            style=req.style,
            duration=req.duration,
            output_path=req.output_path
        )
        return {
            "status": "success",
            "script_path": f"/{req.output_path}",
            "content": script_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-audio")
async def api_generate_audio(req: TTSRequest):
    try:
        text_content = req.text
        if not text_content:
            if not os.path.exists("assets/script.txt"):
                raise HTTPException(status_code=400, detail="No text provided, and assets/script.txt does not exist.")
            with open("assets/script.txt", "r", encoding="utf-8") as f:
                text_content = f.read().strip()
                
        await text_to_speech(
            text=text_content,
            voice=req.voice,
            output_audio=req.output_audio,
            output_srt=req.output_srt
        )
        return {
            "status": "success",
            "audio_path": f"/{req.output_audio}",
            "srt_path": f"/{req.output_srt}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-video")
def api_generate_video(req: VideoRequest):
    try:
        build_video(
            bg_path=req.bg_path,
            audio_path=req.audio_path,
            srt_path=req.srt_path,
            output_path=req.output_path,
            width=req.width,
            height=req.height,
            font_size=req.font_size
        )
        return {
            "status": "success",
            "video_path": f"/{req.output_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-pipeline")
def api_run_pipeline(req: PipelineRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    
    if req.background:
        # Run asynchronously in the background
        background_tasks.add_task(execute_pipeline, task_id, req)
        task_store[task_id] = {"status": "queued", "progress": "waiting to start"}
        return {
            "status": "queued",
            "task_id": task_id,
            "check_status_url": f"/task/{task_id}"
        }
    else:
        # Run synchronously
        logger.info(f"Running synchronous pipeline task: {task_id}")
        execute_pipeline(task_id, req)
        result = task_store.get(task_id, {"status": "failed", "error": "Unknown failure"})
        if result["status"] == "failed":
            raise HTTPException(status_code=500, detail=result.get("error"))
        return result

@app.get("/task/{task_id}")
def check_task_status(task_id: str):
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

if __name__ == "__main__":
    import uvicorn
    # Start FastAPI server on port 8000
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
