import os
import json
import datetime
import requests
import subprocess
from pytube import YouTube, exceptions
from youtubesearchpython import Video, ResultMode
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import WebVTTFormatter


class DownloadOptions:
    def __init__(self, subtitles=True, resolution="Default"):
        self.subtitles = subtitles
        self.resolution = resolution


class DownloadManager:
    def __init__(self, url, options=DownloadOptions()) -> None:
        self.options = options
        self.url = url
        try:
            self.yt = YouTube(
                url,
                on_complete_callback=self.on_complete,
                on_progress_callback=self.on_progress,
            )
        except exceptions.AgeRestrictedError:
            self.yt = YouTube(
                url,
                on_complete_callback=self.on_complete,
                on_progress_callback=self.on_progress,
                use_oauth=True,
                allow_oauth_cache=True,
            )

        dirname = os.path.dirname(__file__)
        self.video_folder = f"{dirname}/static/videos/{self.yt.video_id}"

        if not os.path.exists(self.video_folder):
            os.makedirs(self.video_folder)

        self.metadata = self.__create_meta()
        self.video_info = {}

        with open(os.path.join(self.video_folder, "metadata.json"), "w+") as file:
            json.dump(self.metadata, file)

    def on_complete(self, a, b):
        del self.metadata["progress"]

        if self.options.resolution != "Default":
            video_path = os.path.join(self.video_folder, "video.webm")
            audio_path = os.path.join(self.video_folder, "audio.webm")
            final_video_path = os.path.join(self.video_folder, "video.mp4")
            preview_path = os.path.join(self.video_folder, "preview.mp4")

            if not os.path.exists(video_path):
                return

            self.metadata["status"] = "processing"
            self.__write_meta()

            cmd = f"ffmpeg -i {video_path} -i {audio_path} -c:a copy -c:v copy {final_video_path}"
            with subprocess.Popen(cmd) as process:
                process.wait()

            preview_scale = 480# p
            if (
                self.options.resolution    == "480p"
                or self.options.resolution == "360p"
                or self.options.resolution == "240p"
                or self.options.resolution == "144p"
            ):
                preview_scale = self.options.resolution

            cmd = f'ffmpeg -ss 0 -i {final_video_path} -t 10 {f"-vf scale={preview_scale}:-1:force_original_aspect_ratio=decrease" if preview_scale else ""} {preview_path}'
            with subprocess.Popen(cmd) as process:
                process.wait()

            if process.returncode == 0:
                self.metadata['has_preview'] = True

            os.remove(video_path)
            os.remove(audio_path)

        self.metadata["status"] = "complete"
        self.__write_meta()

    def on_progress(self, vid, chunk, bytes_remaining):
        total_size = vid.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        self.metadata["progress"] = round(percentage_of_completion, 2)

        self.__write_meta()

    def download(self):
        if self.options.subtitles:
            try:
                subtitles = self.get_subtitles(self.yt.video_id)
                with open(
                    os.path.join(self.video_folder, "subtitles_en.vtt"), "w+"
                ) as file:
                    file.write(subtitles)
                    self.metadata["has_subtitles"] = True
            except:
                self.metadata["has_subtitles"] = False

        if self.options.resolution == "Default":
            self.yt.streams.filter(progressive=True, file_extension="mp4").order_by(
                "resolution"
            ).desc().first().download(
                output_path=self.video_folder, filename="video.mp4"
            )
        else:
            self.yt.streams.filter(only_audio=True, file_extension="webm").order_by(
                "bitrate"
            ).desc().first().download(
                output_path=self.video_folder, filename="audio.webm"
            )

            self.yt.streams.filter(adaptive=True, file_extension="webm").filter(
                resolution=self.options.resolution
            ).first().download(output_path=self.video_folder, filename="video.webm")

    def __create_meta(self) -> dict:
        now = datetime.datetime.now()
        self.video_info = Video.getInfo(self.url, mode=ResultMode.json)

        if not os.path.isdir(self.video_folder):
            os.mkdir(self.video_folder)

        with open(os.path.join(self.video_folder, "thumbnail.jpg"), "wb+") as file:
            res = requests.get(self.video_info["thumbnails"][-1]["url"])
            file.write(res.content)

        metadata = {
            "title": self.yt.title,
            "channel": self.video_info["channel"]["name"],
            "duration": self.yt.length,
            "resolution": self.options.resolution,
            "date_downloaded": now.timestamp(),
            # 'date_downloaded': datetime.datetime.strftime(now, "%d/%m/%Y %H:%M:%S"),
            "is_watched": False,
            "status": "downloading",
            "has_subtitles": False,
            "has_preview": False,
            "progress": 0,
        }

        return metadata

    def get_subtitles(self, id, lang="en"):
        transcript = YouTubeTranscriptApi.get_transcript(id, languages=(lang,))
        srt_formatter = WebVTTFormatter()
        return srt_formatter.format_transcript(transcript)

    def __write_meta(self):
        with open(os.path.join(self.video_folder, "metadata.json"), "w+") as file:
            json.dump(self.metadata, file)


if __name__ == "__main__":
    yt = DownloadManager(input("Enter a video url: "))
    yt.download()
