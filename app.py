import os
import json
import time
import shutil
import datetime
import threading
from pathlib import Path
from pytube import YouTube
from flask import Flask, request, render_template, redirect, url_for, make_response, jsonify
from dl_manager import DownloadManager, DownloadOptions
from hurry.filesize import size, alternative
from pprint import pprint

app = Flask(__name__, template_folder="templates")


def get_vids_dir():
    curdir = os.path.dirname(__file__)
    return f"{curdir}/static/videos"


def get_vid_dir(id):
    return os.path.join(get_vids_dir(), id)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    video_url = request.form.get("video-url")
    subtitles = request.form.get("subtitles")
    resolution = request.form.get("resolution")

    print(request.form)
    options = DownloadOptions(
        subtitles=(subtitles != None and subtitles == "on"),
        resolution=("720p" if not resolution else resolution),
    )
    yt = DownloadManager(video_url, options)
    threading.Thread(target=yt.download, daemon=True).start()

    return redirect(url_for("watch"))


@app.route("/watch")
def watch():
    videos_folder = get_vids_dir()

    videos = []
    for dirpath, dirnames, filenames in os.walk(videos_folder):
        for dir in dirnames:
            try:
                with open(os.path.join(dirpath, dir, "metadata.json"), "r") as file:
                    metadata = json.load(file)
                    duration = metadata["duration"]
                    if isinstance(metadata["date_downloaded"], str):
                        metadata["date_downloaded"] = time.mktime(
                            datetime.datetime.strptime(
                                metadata["date_downloaded"], "%d/%m/%Y %H:%M:%S"
                            ).timetuple()
                        )
                    metadata["duration_timestamp"] = time.strftime(
                        ("%H:%M:%S" if duration >= 3600 else "%M:%S"),
                        time.gmtime(duration),
                    )

                video = {"id": dir, "metadata": metadata}
                videos.append(video)
            except Exception as e:
                print(e)

    videos = list(
        sorted(videos, key=lambda v: v["metadata"]["date_downloaded"], reverse=True)
    )
    for v in videos:
        v["metadata"]["date_downloaded"] = datetime.datetime.strftime(
            datetime.datetime.fromtimestamp(v["metadata"]["date_downloaded"]),
            "%d/%m/%Y %H:%M:%S",
        )

    video_id = request.args.get("video")
    video = None
    if video_id:
        filtered_videos = list(filter(lambda v: v["id"] == video_id, videos))
        if not filtered_videos:
            return redirect(url_for("watch"))
        video = filtered_videos[0]

    if video:
        return render_template("watch.html", videos=videos, video=video)

    root_directory = Path(videos_folder)
    total_size = sum(
        f.stat().st_size for f in root_directory.glob("**/*") if f.is_file()
    )
    total_size = size(total_size, alternative)

    return render_template("videos.html", videos=videos, total_size=total_size)


@app.route("/api/watched/<id>", methods=["GET", "POST"])
def api_watched(id):
    video_dir = get_vid_dir(id)

    if not os.path.isdir(video_dir):
        return "Video not found. Invalid ID.", 404

    metadata_path = os.path.join(video_dir, "metadata.json")
    if not os.path.isfile(metadata_path):
        return "Metadata not found.", 410

    with open(metadata_path, "r+") as file:
        metadata = json.load(file)
        if request.method == "GET":
            if "is_watched" not in metadata:
                return "Data not found.", 404
            return str(metadata["is_watched"]).lower()
        else:
            data = request.get_json(True)
            if "state" not in data:
                return "State was not provided.", 400

            metadata["is_watched"] = data["state"]
            file.truncate(0)
            file.seek(0)
            file.write(json.dumps(metadata))

            return "", 204


@app.route("/api/video/<id>", methods=["GET", "DELETE"])
def api_video(id):
    video_dir = get_vid_dir(id)

    if not os.path.exists(video_dir):
        return "Not found. Invalid video ID.", 404

    metadata_path = os.path.join(video_dir, "metadata.json")
    if not os.path.isfile(metadata_path):
        return "Metadata not found.", 410

    with open(metadata_path, "r") as file:
        metadata = json.loads(file.read())

    if request.method == "GET":
        return metadata
    elif request.method == "DELETE":
        for file in os.listdir(video_dir):
            # https://stackoverflow.com/questions/66158631/check-if-a-file-is-written-or-in-use-by-another-process
            try:
                file_path = os.path.join(video_dir, file)
                os.rename(file_path, file_path)
            except:
                return "Resource busy. Try again Later", 503

        shutil.rmtree(video_dir)
        return "", 204


@app.route("/api/pre/resolutions")
def api_pre_resolutions():
    url = request.args.get("url")
    if not url:
        return "Missing URL.", 400

    if "youtube.com" not in url:
        return "Invalid URL.", 400

    yt = YouTube(url)
    available_resolutions = [
        stream.resolution
        for stream in yt.streams.filter(file_extension="webm")
        .order_by("resolution")
        .desc()
    ]

    available_resolutions.insert(0, "Default")

    return jsonify(available_resolutions)


if __name__ == "__main__":
    app.run(threaded=True, host="0.0.0.0", port=9969, debug=True)
