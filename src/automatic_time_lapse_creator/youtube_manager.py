from __future__ import annotations
import os
import json
import tempfile
import logging
import pickle
import smtplib

from typing import Iterable, Any, Generator
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from google.auth.exceptions import RefreshError
from google.auth.external_account_authorized_user import Credentials as Creds
from google.oauth2.credentials import Credentials
from time import sleep

from email.mime.text import MIMEText
from .common.utils import shorten
from .common.logger import configure_child_logger
from .common.constants import (
    AuthMethod,
    VideoPrivacyStatus,
    YOUTUBE_URL_PREFIX,
    MP4_FILE,
    YOUTUBE_MUSIC_CATEGORY,
    YOUTUBE_KEYWORDS,
    MAX_TITLE_LENGTH,
    DEFAULT_CHUNK_SIZE,
)


class YouTubeAuth:
    """
    Service class for authenticating to YouTube Data API v3. 
    A valid clients secrets file should be provided in order to authenticate successfully to YouTube.
    The user has to authenticate manually through a browser window in the initial auth as well as 
    when the credentials expire after a certain amount of time.
    
    Args:
        youtube_client_secrets_file: str - the json secrets file downloaded from the YouTube Data API 
        logger: logging.Logger | None - a logger instance, defaults to None
        auth_method: AuthMethod - authentication via browser locally (default) or via email (not implemented yet)

    Returns:

        YouTubeAuth - a service object for managing the authenticated user's channel.
    """
    def __init__(
            self, 
            youtube_client_secrets_file: str, 
            logger: logging.Logger | None = None, 
            auth_method: AuthMethod = AuthMethod.MANUAL
        ) -> None:

        self.logger = configure_child_logger(logger_name="Authenticator", logger=logger)  
        self.validate_secrets_file(self.logger, youtube_client_secrets_file)

        self.service = self.authenticate_youtube(
            self.logger, youtube_client_secrets_file, auth_method
        )

    @staticmethod
    def validate_secrets_file(
        logger: logging.Logger, secrets_file: str | None
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
        cls, logger: logging.Logger, youtube_client_secrets_file: str, auth_method: AuthMethod
    ) -> Any:
        """Authenticate and return a YouTube service object. If the service is started for the first time or
        the refresh token is expired or revoked, a browser window will open so the user can authenticate manually.
        In the end the credentials will be pickled for future use.
        """
        logger.info("Authenticating with YouTube...")

        credentials: Credentials | Creds | None = None
        pickle_file = os.path.join(
            tempfile.gettempdir(), "youtube-upload-token.pickle"
        )

        if os.path.exists(pickle_file):
            logger.info(f"YouTube auth token file found: {pickle_file}")
            with open(pickle_file, "rb") as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            open_browser_message = "Opening a browser for manual authentication with YouTube..."
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except RefreshError:
                    logger.info(open_browser_message)
                    cls.notify_by_email(logger, message=open_browser_message)
                    credentials = cls.open_browser_to_authenticate(
                        youtube_client_secrets_file, logger, auth_method
                    )
            else:
                logger.info(open_browser_message)
                credentials = cls.open_browser_to_authenticate(
                    youtube_client_secrets_file, logger, auth_method
                )

            with open(pickle_file, "wb") as token:
                logger.info(f"Saving YouTube auth token to file: {pickle_file}")
                pickle.dump(credentials, token)

        return build("youtube", "v3", credentials=credentials)

    @classmethod
    def open_browser_to_authenticate(
        cls, secrets_file: str, logger: logging.Logger, auth_method: AuthMethod
    ) -> Credentials | Creds:
        """
        Authenticates the user with YouTube Data API v3 using either manual browser login
        or email authentication.

        Args:
            secrets_file (str): Path to the Google client secrets JSON.
            logger (logging.Logger): Logger instance for logging events.
            auth_method (str): Authentication method, either 'manual' (default) or 'email'.

        Returns:
            Credentials | Creds: Authenticated YouTube credentials.
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                secrets_file,
                scopes=["https://www.googleapis.com/auth/youtube"]
            )

            # email authentication is not implemented yet! Remotely accessible url should be passed
            # to the InstalledAppFlow.from_client_secrets_file as a redirect_uri parameter
            if auth_method == AuthMethod.EMAIL:
                auth_url, _ = flow.authorization_url(prompt="consent")
                cls.notify_by_email(logger=logger, auth_url=auth_url)
                logger.info("Authentication email sent. Waiting for user approval...")

                while True:
                    try:
                        credentials = flow.run_local_server(port=0)
                        if credentials and credentials.valid:
                            successful_message = "Authentication successful!"
                            logger.info(successful_message)
                            cls.notify_by_email(logger=logger, message=successful_message)
                            return credentials
                    except Exception:
                        pass

                    sleep(10)

            else:
                return flow.run_local_server(port=0)

        except Exception as e:
            unsuccessful_message = "Re-authentication failed."
            logger.error(unsuccessful_message, exc_info=True)
            cls.notify_by_email(logger=logger, message=f"{unsuccessful_message}\n{e}")
            raise RuntimeError(unsuccessful_message) from e

    @staticmethod
    def notify_by_email(logger: logging.Logger, message: str | None = None, auth_url: str | None = None):
        """
        Sends an authentication email containing the YouTube authorization URL.

        Args:
            auth_url (str): The Google authentication URL.
            logger (Logger): Logger instance for logging events.
        """
        sender_email = os.getenv("EMAIL_SENDER", "")
        receiver_email = os.getenv("EMAIL_RECEIVER", "")
        smtp_server = os.getenv("SMTP_SERVER", "")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")

        if any(x == "" for x in [sender_email, receiver_email, smtp_server, smtp_username, smtp_password]):
            logger.error("Email configuration is missing! Please set environment variables.")
            return

        subject = "YouTube Authentication for TimeLapseCreator Required"
        body = f"Click the following link to authenticate: {auth_url}" if not message else message

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, receiver_email, msg.as_string())

            logger.info(f"Authentication email sent to {receiver_email}.")
        except Exception as e:
            logger.error(f"Failed to send authentication email: {e}", exc_info=True)

class YouTubeUpload:
    """Handles uploading videos to YouTube using the YouTube Data API.

    This class manages finding video files, setting metadata, and uploading videos
    to an authenticated YouTube account.

    Attributes::
        source_directory: str - The directory containing the videos to be uploaded.
        youtube_description: str - The description for uploaded videos.
        youtube_title: str - The title for uploaded videos, truncated if necessary.
        youtube_client: YouTubeAuth - The authenticated YouTube API client.
        logger: logging.Logger - The logger instance for logging events and errors.
        input_file_extensions: Iterable[str] - The allowed video file extensions.
        youtube_category_id: str - The category ID for uploaded videos.
        youtube_keywords: Iterable[str] - Tags associated with uploaded videos.
        privacy_status: str - The privacy status of uploaded videos (e.g., public, private).
    """

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
        self.logger = configure_child_logger(logger_name="YouTubeUploader", logger=logger)

        self.youtube = youtube_client

        self.source_directory = source_directory
        self.input_file_extensions = input_file_extensions

        self.youtube_category_id = youtube_category_id
        self.youtube_keywords = youtube_keywords

        self.youtube_description = youtube_description
        self.youtube_title = self.shorten_title(youtube_title)

        self.privacy_status = privacy_status

    def find_input_files(self) -> list[str]:
        """Searches for video files in the specified directory.

        This method scans the `source_directory` for video files that match
        the allowed extensions.

        Returns:
            list[str] - A list of file paths for videos found in the directory.
        """
        video_files = [
            os.path.join(self.source_directory, f)
            for f in os.listdir(self.source_directory)
            if f.endswith(tuple(self.input_file_extensions))
        ]
        if not video_files:
            self.logger.error("No video files found in current directory to upload.")
        else:
            self.logger.info(f"Found {len(video_files)} video files to upload.")

        return video_files

    def shorten_title(self, title: str, max_length: int = MAX_TITLE_LENGTH) -> str:
        """Truncates a video title to ensure it does not exceed YouTube's character limit.

        If the title exceeds `max_length`, it is truncated at the nearest word boundary
        and an ellipsis ("...") is added.

        Args:
            title: str - The original video title.
            max_length: int - The maximum allowed length for the title. Defaults to `MAX_TITLE_LENGTH`.

        Returns:
            str - The truncated title.
        """
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
        """Uploads a video file to YouTube.

        This method sends a video file to YouTube using the YouTube Data API,
        setting its title, description, category, and privacy status.

        Args:
            video_file: str - The path to the video file.
            youtube_title: str - The title of the video.
            youtube_description: str - The description of the video.

        Returns:
            str - The YouTube video ID of the uploaded video.
        """
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
        """Finds video files and uploads them to YouTube.

        This method scans the `source_directory` for video files, uploads them,
        and logs any errors encountered. It returns the details of the first
        successfully uploaded video.

        Returns:
            dict[str, str] - A dictionary containing the uploaded video's title and ID.
                If no videos are uploaded, returns an empty dictionary.
        """
        video_files = self.find_input_files()
        uploaded_videos: list[dict[str, str]] = []
        emtpty_dict: dict[str, str] = {}

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

        return next(iter(uploaded_videos), emtpty_dict)


class YouTubeChannelManager:
    """
    This class manages the YouTube account. It allows retrieving the user's
    YouTube channel details.

    Attributes::

        youtube_client: YouTubeAuth - The authenticated YouTube API client.

        logger: logging.Logger - The logger instance for logging events and errors.
    """

    def __init__(
        self,
        youtube_client: YouTubeAuth,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = configure_child_logger(logger_name="YouTubeChannelManager", logger=logger)
        self.youtube = youtube_client

    def list_channel(self):
        """
        This method queries the YouTube Data API to get the videos of the
        authenticated user's channel.

        Returns:
            Generator[dict[str, str]] | None - A Generator, containing the videos as dict[str, str] if found, otherwise None.
        """
        try:
            self.logger.info("Fetching channel details")
            response = (
                self.youtube.service.search()
                .list(part="id", forMine=True, type="video", maxResults=50)
                .execute()
            )

            video_ids = [item["id"]["videoId"] for item in response.get("items", [])]

            return self.get_video_details(video_ids) if len(video_ids) > 0 else None

        except Exception:
            self.logger.error("Something went wrong", exc_info=True)

    def get_video_details(self, video_ids: list[str]) -> Generator[dict[str, str]]:
        """
        Fetches detailed information about a list of videos given their IDs.

        This method queries the YouTube Data API to retrieve metadata such as title, upload status,
        and privacy status for each video ID provided.

        Args:
            video_ids (list[str]): A list of video IDs to retrieve details for.

        Returns::
            Generator[dict[str, str]]: A Generator of dictionaries, where each dictionary contains:
                - "id": The unique ID of the video.
                - "title": The video's title.
                - "uploadStatus": The upload status of the video (e.g., "uploaded").
                - "privacyStatus": The privacy setting of the video (e.g., "public", "private", or "unlisted").
        """
        response = (
            self.youtube.service.videos()
            .list(part="status,snippet", id=",".join(video_ids))
            .execute()
        )
        videos = response.get("items", [])

        return (
            {
                "id": video["id"],
                "title": video["snippet"]["title"],
                "uploadStatus": video["status"]["uploadStatus"],
                "privacyStatus": video["status"]["privacyStatus"],
            }
            for video in videos
        )
    
    @staticmethod
    def filter_pending_videos(videos: Iterable[dict[str, str]]):
        """Returns the videos with uploadStatus: "uploaded" which is the status of the pending
        videos (failed to upload)

        Args:
            videos (Iterable[dict[str, str]]): the collection of videos returned by get_video_details()

        Returns:
            list[dict[str, str]]: the collection containing only the filtered videos
        """
        return [video for video in videos if video["uploadStatus"] in ["uploaded"]]


    def delete_video(self, video_id: str) -> bool:
        """
        Deletes a video from the authenticated user's YouTube channel.

        This method sends a request to the YouTube Data API to delete the specified video.
        If the deletion is successful, it logs a success message and returns True.
        If an exception occurs, it logs an error message and returns False.

        Args:
            video_id (str): The unique identifier of the YouTube video to be deleted.

        Returns:
            bool: True if the video was successfully deleted, otherwise False.
        """
        try:
            self.youtube.service.videos().delete(id=video_id).execute()

            self.logger.info("Success")
            return True
        except Exception:
            self.logger.error("Failed: ", exc_info=True)
            return False