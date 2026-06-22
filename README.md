# L.I.T.H.O.S.
**Lego Identification Through Home Online Systems**

Point a camera at a LEGO piece → get the part number, name, and image instantly.

---
![Placeholder](https://raw.githubusercontent.com/DreamThief/lithos/refs/heads/main/lithos%20screen.jpg)

## Hardware Required

| Item | Notes |
|------|-------|
| Raspberry Pi 5 | Main unit |
| [Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/) | Connects to CSI port |
| Photo lightbox tent (30cm cube) | Collapsible cube with built-in LEDs and white backdrop — provides even, shadow-free lighting. Search "product photography lightbox" on Amazon (~$20-35) |
| Small screen (optional) | [Official 7" touchscreen](https://www.raspberrypi.com/products/raspberry-pi-touch-display/) or any HDMI display |
| MicroSD card | 16GB+ with Raspberry Pi OS (64-bit) |
|HDMI cable|Mini to micro; the raspberrypi has a micro and the small screens usually need the mini |

---

## Raspberry Pi Setup

### 1. Install Raspberry Pi OS
Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash **Raspberry Pi OS (64-bit)** to your SD card.  
Enable SSH and set your username/password in the imager settings.

### 2. Enable the camera
```bash
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

### 3. Clone and install
```bash
git clone https://github.com/DreamThief/lithos.git /home/$USER/lithos
cd /home/$USER/lithos
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

> **Note:** `picamera2` is a system-level package on Pi OS. The `--system-site-packages` flag is required so the venv can see it. Do not `pip install picamera2`.

### 4. Run the server
```bash
source /home/$USER/lithos/venv/bin/activate
cd /home/$USER/lithos/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000** in Chromium on the Pi, or visit **http://\<pi-ip\>:8000** from any device on your network.

---

## Run at Startup (optional)

Create a systemd service so L.I.T.H.O.S. starts automatically on boot:

```bash
sudo nano /etc/systemd/system/lithos.service
```

Paste:
```ini
[Unit]
Description=L.I.T.H.O.S. LEGO Scanner
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/lithos/backend
ExecStart=/home/YOUR_USERNAME/lithos/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable lithos
sudo systemctl start lithos
```

---

## Development (non-Pi machine)

The camera module gracefully falls back to a placeholder image when `picamera2` is not available, so you can develop and test the UI and identification logic on your laptop.

```bash
cd backend
uvicorn main:app --reload
```

Use the **Upload Image** button to test identification without a physical camera.

---

## Project Structure

```
lithos/
├── backend/
│   ├── main.py         # FastAPI app — routes for stream, scan, upload
│   ├── camera.py       # Camera abstraction (Pi + dev fallback)
│   └── identify.py     # Brickognize API integration
├── frontend/
│   ├── index.html      # Single-page UI
│   ├── style.css       # LEGO-themed dark UI
│   └── app.js          # Fetch calls, result rendering
├── requirements.txt
└── README.md
```

---

## How It Works

1. `camera.py` captures a JPEG frame from the Pi Camera via `picamera2`
2. `identify.py` POSTs the image to the [Brickognize API](https://brickognize.com)
3. Brickognize returns a ranked list of LEGO parts with names, IDs, and reference images
4. The web UI renders the top match with a confidence bar, plus alternative candidates

---

## Keyboard Shortcut

Press **Spacebar** to trigger a scan (same as clicking the SCAN button).
