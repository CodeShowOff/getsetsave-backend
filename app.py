import os
import subprocess
import json
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/info", methods=["POST"])
def get_video_info():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        result = subprocess.run(
            ["yt-dlp", "-J", "--no-playlist", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20
        )

        if result.returncode != 0:
            return jsonify({"error": result.stderr.decode()}), 400

        info = json.loads(result.stdout)
        return jsonify(info)

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout while fetching video info"}), 408

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url")
    format_id = data.get("format_id")

    if not url or not format_id:
        return jsonify({"error": "Missing URL or format_id"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use an output template to let yt-dlp name the file properly.
            out_template = os.path.join(tmpdir, "%(title)s.%(ext)s")
            command = ["yt-dlp", "-f", format_id, "-o", out_template, url]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)

            if result.returncode != 0:
                return jsonify({"error": result.stderr.decode()}), 400

            # Expect that one file is downloaded in the temporary folder.
            files = os.listdir(tmpdir)
            if not files:
                return jsonify({"error": "No file downloaded."}), 500

            downloaded_file = os.path.join(tmpdir, files[0])
            # Use send_file to send the file as an attachment.
            return send_file(downloaded_file, as_attachment=True, attachment_filename=files[0])
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Download timed out"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Listen on all interfaces so Railway (or any hosting) can reach it.
    app.run(host="0.0.0.0", port=5000, debug=True)
