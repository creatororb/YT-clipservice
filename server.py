import os
import shutil
import glob
import tempfile
import asyncio
import subprocess
import logging
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse

# Logging setup
logging.basicConfig(level=logging

