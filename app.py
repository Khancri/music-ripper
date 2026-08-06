import os
import tempfile
import shutil
from flask import Flask, request, jsonify, send_from_directory, after_this_request, send_file
from flask_cors import CORS
import source as music

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route("/download", methods=["POST"])
def download():
    data = request.form
    url = data['url']
    artist = data['artist']
    name = data['name']

    tmpdir = tempfile.mkdtemp()

    @after_this_request
    def cleanup(response):
        shutil.rmtree(tmpdir, ignore_errors=True)
        return response

    file_path = music.download_and_tag(tmpdir, url, artist, name)
    return send_file(file_path, as_attachment=True)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)