import io
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from camera import Camera
from identify import identify_piece

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

camera = Camera()

@asynccontextmanager
async def lifespan(app: FastAPI):
    camera.start()
    logger.info("Camera started")
    yield
    camera.stop()
    logger.info("Camera stopped")

app = FastAPI(title="L.I.T.H.O.S.", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


def mjpeg_generator():
    """Yield MJPEG frames from the camera for live preview."""
    while True:
        frame = camera.get_frame()
        if frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )


@app.get("/stream")
def video_stream():
    """Live MJPEG camera preview."""
    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/scan")
async def scan():
    """Capture a still from the camera and identify the LEGO piece."""
    frame = camera.get_frame()
    if not frame:
        raise HTTPException(status_code=503, detail="Camera not available")

    result = await identify_piece(io.BytesIO(frame), filename="scan.jpg")
    return JSONResponse(result)


@app.post("/zoom")
async def set_zoom(factor: float = Query(..., ge=1.0, le=4.0)):
    """Set camera zoom level. 1.0 = fully zoomed out, 4.0 = 4x zoom."""
    camera.set_zoom(factor)
    return {"zoom": factor}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Identify a LEGO piece from an uploaded image (useful for testing)."""
    data = await file.read()
    result = await identify_piece(io.BytesIO(data), filename=file.filename or "upload.jpg")
    return JSONResponse(result)


# Serve the frontend — must come last so API routes take priority
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
