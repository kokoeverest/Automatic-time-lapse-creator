from __future__ import annotations
import os
import json
import tempfile
import logging
import pickle
from typing import Iterable, Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from google.auth.exceptions import RefreshError
from google.auth.external_account_authorized_user import Credentials as Creds
from google.oauth2.credentials import Credentials

from .common.utils import shorten
from .common.constants import (
    VideoPrivacyStatus,
    YOUTUBE_URL_PREFIX,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOGGING_FORMATTER,
    MP4_FILE,
    YOUTUBE_MUSIC_CATEGORY,
    YOUTUBE_KEYWORDS,
    MAX_TITLE_LENGTH,
    DEFAULT_CHUNK_SIZE,
)


class YouTubeAuth:
    def __init__(self, youtube_client_secrets_file: str) -> None:
        self.logger = logging.getLogger("Authenticator")
        self.validate_secrets_file(self.logger, youtube_client_secrets_file)

        self.service = self.authenticate_youtube(
            self.logger, youtube_client_secrets_file
        )

    @classmethod
    def validate_secrets_file(
        cls, logger: logging.Logger, secrets_file: str | None
    ) -> None:
        """
        Enable youtube upload if client secrets file is provided
        If parsing the file as JSON is successful then the file is a vlid JSON
        """
        if secrets_file is None or not os.path.isfile(secrets_file):
            raise FileNotFoundError(
                f"YouTube client secrets file does not exist: {secrets_file}"
            )

        try:
            with open(secrets_file, "r", encoding="utf-8") as f:
                json.load(f)
                logger.info("YouTube client secrets file is valid JSON")
        except json.JSONDecodeError as e:
            raise Exception(
                f"YouTube client secrets file is not valid JSON: {secrets_file}"
            ) from e

    @classmethod
    def authenticate_youtube(
        cls, logger: logging.Logger, youtube_client_secrets_file: str
    ) -> Any:
        """Authenticate and return a YouTube service object. If the service is started for the first time or
        the refresh token is expired or revoked, a browser window will open so the user can authenticate manually.
        In the end the credentials will be pickled for future use.
        """
        logger.info("Authenticating with YouTube...")

        credentials: Credentials | Creds | None = None
        pickle_file = os.path.join(
            tempfile.gettempdir(), "youtube-bulk-upload-token.pickle"
        )

        if os.path.exists(pickle_file):
            logger.info(f"YouTube auth token file found: {pickle_file}")
            with open(pickle_file, "rb") as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except RefreshError:
                    logger.info(
                        "Opening a browser for manual authentication with YouTube..."
                    )
                    credentials = cls.open_browser_to_authenticate(
                        youtube_client_secrets_file
                    )
            else:
                logger.info(
                    "Opening a browser for manual authentication with YouTube..."
                )
                credentials = cls.open_browser_to_authenticate(
                    youtube_client_secrets_file
                )

            with open(pickle_file, "wb") as token:
                logger.info(f"Saving YouTube auth token to file: {pickle_file}")
                pickle.dump(credentials, token)

        return build("youtube", "v3", credentials=credentials)

    @classmethod
    def open_browser_to_authenticate(cls, secrets_file: str) -> Credentials | Creds:
        """Trigger browser-based authentication and return new credentials."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                secrets_file,
                scopes=["https://www.googleapis.com/auth/youtube"],
            )
            return flow.run_local_server(port=0)
        except Exception as e:
            raise RuntimeError("Re-authentication failed.") from e


class YouTubeUpload:
    def __init__(
        self,
        source_directory: str,
        youtube_description: str,
        youtube_title: str,
        youtube_client: YouTubeAuth,
        logger: logging.Logger | None = None,
        input_file_extensions: Iterable[str] = [MP4_FILE],
        youtube_category_id: str = YOUTUBE_MUSIC_CATEGORY,
        youtube_keywords: Iterable[str] = YOUTUBE_KEYWORDS,
        privacy_status: str = VideoPrivacyStatus.PUBLIC.value,
    ) -> None:
        if logger is None:
            self.logger = logging.getLogger("YouTubeUploader")
            self.logger.setLevel(DEFAULT_LOG_LEVEL)
            self.log_formatter = DEFAULT_LOGGING_FORMATTER
        else:
            self.logger = logger

        if not self.logger.hasHandlers():
            _log_handler = logging.StreamHandler()

            _log_handler.setFormatter(DEFAULT_LOGGING_FORMATTER)
            self.logger.addHandler(_log_handler)

        self.youtube = youtube_client

        self.source_directory = source_directory
        self.input_file_extensions = input_file_extensions

        self.youtube_category_id = youtube_category_id
        self.youtube_keywords = youtube_keywords

        self.youtube_description = youtube_description
        self.youtube_title = self.shorten_title(youtube_title)

        self.privacy_status = privacy_status

    def find_input_files(self) -> list[str]:
        video_files = [
            os.path.join(self.source_directory, f)
            for f in os.listdir(self.source_directory)
            if f.endswith(tuple(self.input_file_extensions))
        ]
        if not video_files:
            self.logger.error("No video files found in current directory to upload.")

        self.logger.info(f"Found {len(video_files)} video files to upload.")

        return video_files

    def get_channel_id(self) -> str | None:
        # Get the authenticated user's channel
        request = self.youtube.service.channels().list(part="snippet", mine=True)
        response = request.execute()

        # Extract the channel ID
        if "items" in response:
            channel_id = response["items"][0]["id"]
            return channel_id
        else:
            return None

    def shorten_title(self, title: str, max_length: int = MAX_TITLE_LENGTH) -> str:
        if len(title) <= max_length:
            return title

        truncated_title = title[:max_length].rsplit(" ", 1)[0]
        if len(truncated_title) < max_length:
            truncated_title += " ..."

        self.logger.debug(
            f"Truncating title with length {len(title)} to: {truncated_title}"
        )
        return truncated_title

    def upload_video_to_youtube(
        self,
        video_file: str,
        youtube_title: str,
        youtube_description: str,
    ) -> str:
        self.logger.info(f"Uploading video {shorten(video_file)} to YouTube...")
        body: dict[str, dict[str, str | Iterable[str]]] = {
            "snippet": {
                "title": youtube_title,
                "description": youtube_description,
                "tags": self.youtube_keywords,
                "categoryId": self.youtube_category_id,
            },
            "status": {"privacyStatus": self.privacy_status},
        }

        media_file = MediaFileUpload(
            video_file, resumable=True, chunksize=DEFAULT_CHUNK_SIZE
        )

        # Call the API's videos.insert method to create and upload the video.
        request = self.youtube.service.videos().insert(
            part="snippet,status", body=body, media_body=media_file
        )

        response = None
        while response is None:
            _, response = request.next_chunk()

        youtube_video_id = response.get("id")
        youtube_url = f"{YOUTUBE_URL_PREFIX}{youtube_video_id}"
        self.logger.info(f"Uploaded video to YouTube: {youtube_url}")

        return youtube_video_id

    def process(self) -> dict[str, str]:
        video_files = self.find_input_files()
        uploaded_videos: list[dict[str, str]] = []
        for video_file in video_files:
            try:
                youtube_id = self.upload_video_to_youtube(
                    video_file, self.youtube_title, self.youtube_description
                )
                uploaded_videos.append(
                    {
                        "youtube_title": self.youtube_title,
                        "youtube_id": youtube_id,
                    }
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to upload video {shorten(video_file)} to YouTube: {e}"
                )

        return next(iter(uploaded_videos))
