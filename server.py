import os
import subprocess
import tempfile
import logging
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

API_KEY = os.getenv("API_KEY")  # Optional if you want to secure your endpoint

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/download")
async def download(request: Request, background_tasks: BackgroundTasks):
    """
    Expects JSON:
    {
        "url": "YOUTUBE_URL",
        "start": 10,
        "end": 20
    }
    """
    try:
        body = await request.json()
        url = body.get("url")
        start = body.get("start")
        end = body.get("end")

        if not url or start is None or end is None:
            raise HTTPException(status_code=400, detail="Missing url/start/end")

        logger.info(f"Download request: url={url}, start={start}, end={end}")

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, "input.%(ext)s")
            output_file = os.path.join(tmpdir, "clip.mp4")

            # Download video using yt-dlp
            subprocess.run([
                "yt-dlp", "-f", "mp4", "-o", input_file, url
            ], check=True)

            # Find the downloaded file (yt-dlp replaces %(ext)s)
            downloaded_files = [f for f in os.listdir(tmpdir) if f.startswith("input.")]
            if not downloaded_files:
                raise HTTPException(status_code=500, detail="Download failed")
            input_path = os.path.join(tmpdir, downloaded_files[0])

            # Trim video with ffmpeg
            subprocess.run([
                "ffmpeg", "-i", input_path, "-ss", str(start), "-to", str(end),
                "-c", "copy", output_file
            ], check=True)

            # Return clip to client
            return FileResponse(output_file, filename="clip.mp4", media_type="video/mp4")

    except subprocess.CalledProcessError as e:
        logger.exception("Subprocess failed")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Error in /download")
        raise HTTPException(status_code=500, detail=str(e))

