from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
import os
import instaloader
import requests
import threading
import time

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Function to delete files after 2 minutes
def cleanup_files():
    while True:
        time.sleep(120)  # Wait for 2 minutes
        now = time.time()
        for filename in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            if os.path.isfile(file_path) and now - os.path.getctime(file_path) > 120:
                os.remove(file_path)
                print(f"Deleted {filename}")

# Start the cleanup thread
threading.Thread(target=cleanup_files, daemon=True).start()

@app.route('/download', methods=['POST'])
def download_reel():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Extract shortcode safely
        shortcode = url.rstrip('/').rsplit("/", 2)[-1]

        # Fetch Reel metadata
        loader = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        video_url = post.video_url
        thumbnail_url = post.url  # Thumbnail
        video_name = post.shortcode  # Unique ID

        # Download video safely
        video_filename = f"video_{video_name}.mp4"
        video_path = os.path.join(DOWNLOAD_FOLDER, video_filename)

        response = requests.get(video_url, stream=True)
        with open(video_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)

        # Generate video URL dynamically
        video_serving_url = url_for('serve_video', filename=video_filename, _external=True)

        return jsonify({
            'video_url': video_serving_url,
            'thumbnail_url': thumbnail_url,
            'video_name': f"Reel {video_name}"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
