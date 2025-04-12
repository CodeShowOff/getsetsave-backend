from flask import Flask, request, jsonify, send_file
import subprocess
import json
import tempfile
import os
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
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "%(title)s.%(ext)s")

            result = subprocess.run(
                ["yt-dlp", "-f", format_id, "-o", output_path, url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )

            if result.returncode != 0:
                return jsonify({"error": result.stderr.decode()}), 400

            # Find downloaded file
            for file_name in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file_name)
                return send_file(file_path, as_attachment=True)

            return jsonify({"error": "Download failed"}), 500

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Download timed out"}), 408

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
