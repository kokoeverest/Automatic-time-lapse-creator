from __future__ import annotations
import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from multiprocessing import Process, Queue
from queue import Empty
import wsgiref.simple_server
import wsgiref.util
from urllib3.util import parse_url
from time import sleep

from typing import Iterable, Any, Generator
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.external_account_authorized_user import Credentials as Creds

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
    DEFAULT_EMAIL_AUTH_TIMEOUT_SECONDS
)


class YouTubeAuth:
    """
    Service class for authenticating to YouTube Data API v3. 
    A valid clients secrets file should be provided in order to authenticate successfully to YouTube.
    The user has to authenticate manually through a browser window in the initial auth as well as 
    when the credentials expire after a certain amount of time.
    
    Args:
        youtube_client_secrets_file: str - the json secrets file downloaded from the YouTube Data API 
        token_file_name: str - a file name under which the credentials will be saved locally
        logger: logging.Logger | None - a logger instance, defaults to None
        auth_method: AuthMethod - authentication via browser locally (default) or via email
        redirect_url: str | None - url at which the email authentication will return the credentials
        email_auth_timeout_seconds: int - timeout to wait for email authentication

    Returns:

        YouTubeAuth - a service object for managing the authenticated user's channel.
    """
    def __init__(
            self, 
            youtube_client_secrets_file: str,
            token_file_name: str,
            logger: logging.Logger | None = None, 
            auth_method: AuthMethod = AuthMethod.MANUAL,
            redirect_url: str | None = None,
            email_auth_timeout_seconds: int = DEFAULT_EMAIL_AUTH_TIMEOUT_SECONDS
        ) -> None:
        self.redirect_url = None
        
        if auth_method == AuthMethod.EMAIL:
            if not redirect_url:
                raise ValueError("redirect_url required for EMAIL auth.")
            else:
                self.redirect_url = redirect_url

        self.logger = configure_child_logger(logger_name="Authenticator", logger=logger)  
        self.validate_secrets_file(self.logger, youtube_client_secrets_file)
        
        if len(token_file_name) == 0:
            self.logger.warning("Token file name is an empty string!")
        self.token_file_name = token_file_name
        self.auth_method = auth_method
        self.email_auth_timeout_seconds = email_auth_timeout_seconds
        
        self.service = self.authenticate_youtube(youtube_client_secrets_file)

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

    def authenticate_youtube(self, youtube_client_secrets_file: str) -> Any:
        self.logger.info("Authenticating with YouTube...")

        credentials = None
        token_file = os.path.join(os.path.dirname(youtube_client_secrets_file), self.token_file_name)

        if os.path.exists(token_file):
            self.logger.info(f"YouTube auth token found: {token_file}")
            try:
                credentials = Credentials.from_authorized_user_file(token_file)
            except Exception:
                self.logger.warning("Token file is corrupted or invalid. Re-authenticating...")
                credentials = None

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception:
                    self.logger.info("Token expired/invalid. Re-authenticating...")
                    credentials = self.open_browser_to_authenticate(youtube_client_secrets_file)
            else:
                credentials = self.open_browser_to_authenticate(youtube_client_secrets_file)

            # Save the new token as JSON
            with open(token_file, "w") as token:
                token.write(credentials.to_json())

        return build("youtube", "v3", credentials=credentials)

    @staticmethod
    def _auth_worker(
        secrets_file: str, 
        scopes: list[str], 
        host: str, 
        port: int, 
        redirect_url: str, 
        queue: Queue[Any], 
        logger: logging.Logger, 
        cls: type[YouTubeAuth]
        ):
        try:
            # 1. Initialize flow inside the worker for state isolation
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, scopes=scopes)
            flow.redirect_uri = redirect_url
            
            # 2. Generate the Auth URL and capture the state correctly
            auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")
            
            # 3. Send the email
            try:
                cls.notify_by_email(logger=logger, auth_url=auth_url)
                # Check if the email actually worked (or just log it properly)
                logger.info(f"Worker initiated auth sequence. State: {state}")
            except Exception as e:
                logger.error(f"Worker failed to send email: {e}")

            # 4. Define a simple, standalone WSGI App
            class SimpleAuthApp:
                def __init__(self):
                    self.last_request_uri = None
                def __call__(self, environ, start_response):
                    start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
                    self.last_request_uri = wsgiref.util.request_uri(environ)
                    return [b"Authentication successful! You can now close this tab."]

            # 5. Define a silent request handler
            class SilentHandler(wsgiref.simple_server.WSGIRequestHandler):
                def log_message(self, format, *args):
                    pass

            # 6. Start the local server
            auth_app = SimpleAuthApp()
            local_server = wsgiref.simple_server.make_server(
                host, port, auth_app, handler_class=SilentHandler
            )
            
            local_server.handle_request()
            
            auth_response = auth_app.last_request_uri.replace('http:', 'https:')
            flow.fetch_token(authorization_response=auth_response)
            
            queue.put(flow.credentials)
        except Exception as e:
            logger.error(f"Worker failed: {e}", exc_info=True)
            queue.put(e)

    def open_browser_to_authenticate(self, secrets_file: str) -> Credentials | Creds:
        # Use the scopes required for YouTube
        scopes = ["https://www.googleapis.com/auth/youtube"]
        
        try:
            if self.auth_method == AuthMethod.EMAIL and self.redirect_url:
                parsed_url = parse_url(self.redirect_url)
                port = parsed_url.port or 8080
                _host: str = "0.0.0.0"

                queue: Queue[Any] = Queue()
                process = Process(
                    target=self._auth_worker, 
                    args=(
                        secrets_file, 
                        scopes, 
                        _host, 
                        port, 
                        self.redirect_url, 
                        queue, 
                        self.logger, 
                        self.__class__
                    )
                )
                process.start()

                # Instead of joining first, we wait on the QUEUE.
                # This breaks the deadlock because the parent reads while the child is alive.
                try:
                    timeout = getattr(self, 'email_auth_timeout_seconds', 3600)
                    result = queue.get(timeout=timeout) 
                except Empty:
                    # If we hit the timeout without getting data
                    if process.is_alive():
                        process.terminate()
                    raise RuntimeError("YouTube Authentication timed out.")
                finally:
                    # Always join at the very end to clean up the process
                    if process.is_alive():
                        process.join(timeout=5)
                if isinstance(result, Exception):
                    raise result
                return result

            else:
                # Standard manual flow
                flow = InstalledAppFlow.from_client_secrets_file(secrets_file, scopes=scopes)
                return flow.run_local_server(port=0)

        except Exception as e:
            msg = f"YouTube Authentication failed: {str(e)}"
            self.logger.error(msg, exc_info=True)
            # Notify user of failure if email was the intended method
            if self.auth_method == AuthMethod.EMAIL:
                self.notify_by_email(logger=self.logger, message=msg)
            # Avoid double-wrapping intentional RuntimeErrors (e.g. timeout)
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(msg) from e

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
        
        try:
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
        except ValueError:
            logger.error("SMTP_PORT environment variable is missing or invalid.")
            return

        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")

        # Configuration Check
        if not all([sender_email, receiver_email, smtp_server, smtp_username, smtp_password]):
            logger.error("Email configuration is incomplete. Check your environment variables.")
            return

        subject = "YouTube Authentication Required"
        body = f"Authorize here: {auth_url}" if not message else message
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Added a 10-second timeout to the connection attempt
                with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.sendmail(sender_email, receiver_email, msg.as_string())
                
                logger.info(f"Authentication email successfully sent to {receiver_email}.")
                return  # Success, exit the retry loop
                
            except (smtplib.SMTPConnectError, ConnectionRefusedError, TimeoutError) as e:
                logger.warning(f"Email attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    sleep(5)  # Wait 5 seconds before retrying
                else:
                    logger.error("All email retry attempts failed.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while sending email: {e}", exc_info=True)
                break

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
                if "quotaExceeded" in str(e):
                    self.logger.warning("Quota exceeded! Breaking")
                    raise e

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