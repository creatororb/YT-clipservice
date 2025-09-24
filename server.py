import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@app.post("/download")
async def download(request: Request, background_tasks: BackgroundTasks):
    try:
        # Get JSON from the request
        body = await request.json()
        url = body.get("url")
        start = body.get("start")
        end = body.get("end")

        # Validate input
        if not url or start is None or end is None:
            raise HTTPException(status_code=400, detail="Missing url/start/end")

        # Log the request
        logger.info(f"Download request received: url={url}, start={start}, end={end}")

        # --- your video processing code goes here ---
        # For now, just return a dummy success
        return {"status": "processing", "url": url, "start": start, "end": end}

    except Exception as e:
        # Log the full traceback in Render logs
        logger.exception("Error in /download endpoint")
        # Return a 500 error to the client
        raise HTTPException(status_code=500, detail=str(e))
import os
import shutil
import glob
import tempfile
import asyncio
import subprocess
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse

# Create the FastAPI app
app = FastAPI()

API_KEY = os.getenv("API_KEY")  # optional for security

# Cleanup function
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

    tmpdir = tempfile.mkdtemp(prefix="ytd-")
    background_tasks.add_task(cleanup_dir, tmpdir)

    out_template = os.path.join(tmpdir, "video.%(ext)s")
    ytdlp_cmd = [
        "yt-dlp", "-f", "best", "--merge-output-format", "mp4",
        "-o", out_template, url
    ]
    await asyncio.to_thread(subprocess.run, ytdlp_cmd, check=True, cwd=tmpdir)

    matches = glob.glob(os.path.join(tmpdir, "video.*"))
    if not matches:
        raise HTTPException(status_code=500, detail="No video file found")
    input_path = matches[0]

    if start is not None or end is not None:
        start_sec = float(start) if start else 0.0
        duration = (float(end) - start_sec) if end else None
        out_clip = os.path.join(tmpdir, "clip.mp4")

        ff_cmd = ["ffmpeg", "-y"]
        if start_sec:
            ff_cmd += ["-ss", str(start_sec)]
        ff_cmd += ["-i", input_path]
        if duration:
            ff_cmd += ["-t", str(duration)]
        ff_cmd += ["-c", "copy", out_clip]

        try:
            await asyncio.to_thread(subprocess.run, ff_cmd, check=True)
            output_path = out_clip
        except subprocess.CalledProcessError:
            raise HTTPException(status_code=500, detail="ffmpeg failed")
    else:
        output_path = input_path

    return FileResponse(
        output_path,
        filename=os.path.basename(output_path),
        media_type="video/mp4"
    )

