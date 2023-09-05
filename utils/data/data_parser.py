import argparse
from pathlib import Path
from moviepy.editor import AudioFileClip
from typing import Union, Callable
from pytube import YouTube
from tqdm import tqdm
import csv


class DataParser:
    """
    Class DataParser for downloading and converting YouTube videos into specified audio format.

    Attributes:
        file_with_ids (Path): Path to the file containing YouTube IDs.
        save_to (Path): Directory path to save audio files.
        source (str): Source of the data (e.g. "YouTube").
        audio_format (str): Desired audio file format (default: "wav").
        batch (bool): Whether to save audio in batches or not (default: False).
        batch_seconds (int): Length of each audio batch in seconds (default: 30).

    Methods:
        download_and_convert: Downloads a YouTube video and converts it to the specified audio file format.
        segment_audio: Segments an audio file into specified length.
        process: Processes each YouTube ID from the CSV file provided.
    """
    def __init__(self, file_with_ids: Union[str, Path], save_to: Union[str, Path], source: str,
                 audio_format: str = "wav", batch: bool = False, batch_seconds: int = 30) -> None:
        self.file_with_ids = Path(file_with_ids)
        self.save_to = Path(save_to)
        self.source = source
        self.audio_format = audio_format
        self.batch = batch
        self.batch_seconds = batch_seconds
        self.downloader: Callable = self.get_downloader()
        self.process()

    def get_downloader(self) -> Callable:
        """
        Get the appropriate downloader method based on the source.
        :return: Callable: Class method for the appropriate data source.
        """
        if self.source == "youtube":
            return self.download_from_youtube
        # We can add support for other data sources in future (e.g. Cloud Based Storages etc.)
        else:
            raise ValueError(f"Unsupported data source: {self.source}")

    def download_from_youtube(self, video_id: str) -> Path:
        """
        Downloads a YouTube video, converts it to the audio, and return the audio file path.
        :param video_id: (str) The video id for YouTube video.
        :return: (Path) The file path where was audio saved.
        """
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        stream = yt.streams.filter(only_audio = True).first()
        audio_path = self.save_to / f"{yt.title}.{self.audio_format}"
        stream.download(output_path = str(self.save_to), filename = yt.title)
        return audio_path.with_suffix(f".{self.audio_format}")

    def segment_audio(self, audio_path: Path) -> None:
        """
        Segments an audio file into chunks of specified length.
        :param audio_path: Path to the audio file.
        :return: None
        """
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        for i in range(0, int(duration), self.batch_seconds):
            start = i
            end = i + self.batch_seconds if i + self.batch_seconds < duration else duration
            segment_filename = f"{audio_path.stem}_segment_{i // self.batch_seconds + 1}{audio_path.suffix}"
            audio.subclip(start, end).write_audiofile(str(self.save_to / segment_filename))

    def process(self) -> None:
        """Process each video ID from the CSV file with progress tracking."""
        video_ids = []
        with self.file_with_ids.open('r') as file:
            reader = csv.reader(file)
            for row in reader:
                video_ids.append(row[0])

        for video_id in tqdm(video_ids, desc="Downloading and processing videos"):
            audio_path = self.downloader(video_id)
            if self.batch:
                self.segment_audio(audio_path)


def main():
    """CLI for downloading and processing videos from various sources."""
    parser = argparse.ArgumentParser(description = 'Download videos and convert them to audio format.')
    parser.add_argument('--file_with_ids', type = str, required = True, help = 'Path to the file with video IDs.')
    parser.add_argument('--save_to', type = str, required = True, help = 'Path to save the downloaded audio files.')
    parser.add_argument('--source', type = str, default = 'youtube', choices = ['youtube'],
                        help = 'Source of the videos. Currently supports only YouTube.')
    parser.add_argument('--audio_format', type = str, default = 'wav', choices = ['wav', 'mp3'],
                        help = 'Desired audio format to save the files.')
    parser.add_argument('--batch', action = 'store_true', help = 'Save the audio in batches of specified duration.')
    parser.add_argument('--batch_seconds', type = int, default = 30,
                        help = 'Duration of each batch in seconds if batch mode is activated.')

    args = parser.parse_args()

    data_parser = DataParser(
        file_with_ids = Path(args.file_with_ids),
        save_to = Path(args.save_to),
        source = args.source,
        audio_format = args.audio_format,
        batch = args.batch,
        batch_seconds = args.batch_seconds
    )

    data_parser.process()


if __name__ == "__main__":
    main()
