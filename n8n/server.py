import os
import uuid
import logging
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
    description="Orchestrator server for subtitle-overlaid video generation workflows with local Ollama support.",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure jobs base directories exist
os.makedirs("assets/jobs", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Global in-memory job store
jobs_db = {}

# Request Models
class PipelineRequest(BaseModel):
    topic: str = Field(..., json_schema_extra={"example": "3 shocking facts about deep ocean life"})
    style: str = Field("engaging, informative, fast-paced", json_schema_extra={"example": "mysterious, cinematic"})
    duration: str = Field("60 seconds", json_schema_extra={"example": "30 seconds"})
    voice: str = Field("en-US-AvaNeural", json_schema_extra={"example": "en-US-AndrewNeural"})
    bg_path: str = Field("assets/bg.mp4", description="Path to background video (optional)")
    font_size: int = Field(60, json_schema_extra={"example": 65})
    ollama_model: str = Field("llama3.1", description="Local Ollama model name to try first")
    ollama_url: str = Field("http://localhost:11434/api/generate", description="Local Ollama HTTP endpoint")

def run_job_pipeline(job_id: str, req: PipelineRequest):
    """
    Executes script, TTS, and video rendering sequentially in the background.
    All outputs are saved under assets/jobs/{job_id}/ to prevent overlaps.
    """
    job_dir = f"assets/jobs/{job_id}"
    os.makedirs(job_dir, exist_ok=True)
    
    script_path = os.path.join(job_dir, "script.txt")
    audio_path = os.path.join(job_dir, "voice.mp3")
    srt_path = os.path.join(job_dir, "voice.srt")
    video_path = os.path.join(job_dir, "final.mp4")

    try:
        # Step 1: Script Generation (with Ollama prioritisation)
        jobs_db[job_id] = {"status": "processing", "progress": "generating script"}
        logger.info(f"Job {job_id}: Generating script...")
        script_text = generate_script(
            topic=req.topic,
            style=req.style,
            duration=req.duration,
            output_path=script_path,
            ollama_model=req.ollama_model,
            ollama_url=req.ollama_url
        )
        
        # Step 2: TTS Generation
        jobs_db[job_id] = {"status": "processing", "progress": "generating speech audio"}
        logger.info(f"Job {job_id}: Generating audio and subtitles...")
        asyncio.run(text_to_speech(
            text=script_text,
            voice=req.voice,
            output_audio=audio_path,
            output_srt=srt_path
        ))
        
        # Step 3: Video compositing
        jobs_db[job_id] = {"status": "processing", "progress": "rendering composite video"}
        logger.info(f"Job {job_id}: Rendering subtitle layer and video...")
        build_video(
            bg_path=req.bg_path,
            audio_path=audio_path,
            srt_path=srt_path,
            output_path=video_path,
            width=1080,
            height=1920,
            font_size=req.font_size
        )
        
        # Mark complete
        jobs_db[job_id] = {
            "status": "completed",
            "progress": "done",
            "video_path": video_path
        }
        logger.info(f"Job {job_id}: Render completed successfully.")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs_db[job_id] = {
            "status": "failed",
            "progress": "error",
            "error": str(e)
        }

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Automated Video Pipeline Server v2.1 (Ollama-first & Job-based polling model)",
        "endpoints": {
            "/run-pipeline": "POST",
            "/status/{job_id}": "GET",
            "/download/{job_id}": "GET"
        }
    }

@app.post("/run-pipeline")
def run_pipeline(req: PipelineRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:12] # Generate unique job ID
    
    # Initialize job state
    jobs_db[job_id] = {
        "status": "processing",
        "progress": "queued"
    }
    
    # Run pipeline in background
    background_tasks.add_task(run_job_pipeline, job_id, req)
    
    return {
        "status": "processing",
        "job_id": job_id
    }

@app.get("/status/{job_id}")
def get_job_status(job_id: str):
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return job

@app.get("/download/{job_id}")
def download_job_video(job_id: str):
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
        
    if job["status"] == "processing":
        raise HTTPException(status_code=400, detail="Video is still rendering. Please check /status/ again soon.")
    elif job["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"Job failed: {job.get('error')}")
        
    video_path = job.get("video_path")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Generated video file not found on disk")
        
    return FileResponse(video_path, media_type="video/mp4", filename=f"final_{job_id}.mp4")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
