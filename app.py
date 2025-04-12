from flask import Flask, request, jsonify, Response
import subprocess
import json
from flask_cors import CORS
import requests

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
def download_proxy():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "No download URL provided"}), 400

    try:
        # Stream content from the source URL
        with requests.get(url, stream=True) as r:
            headers = {
                'Content-Disposition': 'attachment; filename="download"',
                'Content-Type': r.headers.get('Content-Type', 'application/octet-stream')
            }
            return Response(r.iter_content(chunk_size=8192), headers=headers)
    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
