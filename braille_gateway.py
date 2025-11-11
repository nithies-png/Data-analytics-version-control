"""
braille_gateway.py
---------------------------------
Local gateway that:
 - Watches incoming_messages/ for new .txt or .wav files
 - Runs your unified_braille_processor.py to convert to Grade-2 Braille
 - Optionally receives WhatsApp messages via Twilio webhook (/whatsapp)
 - Displays and logs Braille output locally
"""

import os, time, threading, requests
from pathlib import Path
from flask import Flask, request, jsonify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import your processing module
import unified_braille_processor as ubp

# Folders
INBOX = Path("incoming_messages");  INBOX.mkdir(exist_ok=True)
OUTBOX = Path("processed_outputs"); OUTBOX.mkdir(exist_ok=True)
LOG = OUTBOX / "braille_log.txt"

# -------------------- Utility Functions --------------------

def log_output(text, braille, src="local"):
    entry = f"\n---\nSource: {src}\nText: {text}\nBraille: {braille}\n"
    with open(LOG, "a", encoding="utf8") as f:
        f.write(entry)
    print(entry)

def display_braille(braille):
    print("\n=== BRAILLE OUTPUT ===")
    print(braille)
    print("======================\n")
    (OUTBOX / "latest_braille.txt").write_text(braille, encoding="utf8")

# -------------------- Local Processing --------------------

def process_text_file(path: Path):
    """Uses your process_text_file() or translate_to_simplified_braille()."""
    try:
        if hasattr(ubp, "process_text_file"):
            braille = ubp.process_text_file(str(path))
            if isinstance(braille, tuple):
                text, braille = braille
            else:
                text = path.read_text(encoding="utf8")
        else:
            text = path.read_text(encoding="utf8")
            braille = ubp.translate_to_simplified_braille(text)
        display_braille(braille)
        log_output(text, braille, "text file")
    except Exception as e:
        print("❌ Error processing text file:", e)

def process_audio_file(path: Path):
    """Uses your process_audio_file() for transcription + braille conversion."""
    try:
        if hasattr(ubp, "process_audio_file"):
            text, braille = ubp.process_audio_file(str(path))
            display_braille(braille)
            log_output(text, braille, "audio file")
        else:
            print("process_audio_file() not found in unified_braille_processor.")
    except Exception as e:
        print("❌ Error processing audio file:", e)

# -------------------- Folder Watcher --------------------

class Watcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory: return
        p = Path(event.src_path)
        time.sleep(0.2)
        if p.suffix.lower() in [".txt"]:
            process_text_file(p);  p.unlink(missing_ok=True)
        elif p.suffix.lower() in [".wav", ".mp3", ".ogg", ".m4a"]:
            process_audio_file(p); p.unlink(missing_ok=True)
        else:
            print("Ignored file:", p.name)

def start_watcher():
    obs = Observer()
    obs.schedule(Watcher(), str(INBOX), recursive=False)
    obs.start()
    print("📂 Watching folder:", INBOX)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: obs.stop()
    obs.join()

# -------------------- Flask Webhook for Twilio --------------------

app = Flask(__name__)

def download_media(url, dest):
    try:
        r = requests.get(url, stream=True, timeout=15); r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192): f.write(chunk)
        return True
    except Exception as e:
        print("❌ Download error:", e); return False

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.form.get("Body", "").strip()
    media_url = request.form.get("MediaUrl0")
    media_type = request.form.get("MediaContentType0", "")
    if media_url and "audio" in media_type:
        fname = INBOX / f"msg_{int(time.time())}.ogg"
        if download_media(media_url, fname): process_audio_file(fname)
        return jsonify({"ok": True})
    elif body:
        fname = INBOX / f"msg_{int(time.time())}.txt"
        fname.write_text(body, encoding="utf8")
        process_text_file(fname)
        return jsonify({"ok": True})
    return jsonify({"ok": False})

# -------------------- Main Runner --------------------

def main():
    t = threading.Thread(target=start_watcher, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    main()
