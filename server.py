import os
import shutil
import tempfile
import asyncio
import subprocess
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse

# Create the FastAPI app
app = FastAPI()

API_KEY = os.getenv("API_KEY")  # optional for security

def cleanup_dir(path: str):
    try:
        shutil.rmtree(path)
    except Exception:
        pass

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/download")
async def download(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    url = body.get("url")
    start = body.get("start")
    end = body.get("end")

    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url'")

    # Create a temporary directory
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, "clip.mp4")

    # Download and trim video using yt-dlp and ffmpeg
    cmd = [
        "yt-dlp",
        "-f", "mp4",
        "-o", os.path.join(tmp_dir, "%(title)s.%(ext)s"),
        url
    ]
    subprocess.run(cmd, check=True)

    # For simplicity, assume first downloaded file is the video
    video_file = next(iter(os.listdir(tmp_dir)))
    video_path = os.path.join(tmp_dir, video_file)

    trim_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-ss", str(start),
        "-to", str(end),
        "-c", "copy",
        output_path
    ]
    subprocess.run(trim_cmd, check=True)

    # Cleanup original downloaded file
    os.remove(video_path)

    # Schedule cleanup
    background_tasks.add_task(cleanup_dir, tmp_dir)

    return FileResponse(
        output_path,
        filename=os.path.basename(output_path),
        media_type="video/mp4"
    )

