from logging import Logger
from typing import Any, Generator, Iterable
from google.auth.external_account_authorized_user import Credentials as Creds
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource
from .common.constants import AuthMethod

class YouTubeAuth:
    logger: Logger
    service: Resource
    def __init__(self, youtube_client_secrets_file: str, logger: Logger | None = ..., auth_method: AuthMethod = ...) -> None: ...
    @staticmethod
    def validate_secrets_file(logger: Logger, secrets_file: str | None) -> None: ...
    @classmethod
    def authenticate_youtube(
        cls, logger: Logger, youtube_client_secrets_file: str, auth_method: AuthMethod
    ) -> Any: ...
    @classmethod
    def open_browser_to_authenticate(cls, secrets_file: str, auth_method: AuthMethod) -> Credentials | Creds: ...
    @staticmethod
    def notify_by_email(logger: Logger, message: str | None = ..., auth_url: str | None = ...) -> None: ...
    
class YouTubeUpload:
    logger: Logger
    youtube: YouTubeAuth
    source_directory: str
    input_file_extensions: Iterable[str]
    youtube_category_id: str
    youtube_keywords: Iterable[str]
    youtube_description: str
    youtube_title: str
    privacy_status: str
    def __init__(
        self,
        source_directory: str,
        youtube_description: str,
        youtube_title: str,
        youtube_client: YouTubeAuth,
        logger: Logger | None = ...,
        input_file_extensions: Iterable[str] = ...,
        youtube_category_id: str = ...,
        youtube_keywords: Iterable[str] = ...,
        privacy_status: str = ...,
    ) -> None: ...
    def find_input_files(self) -> list[str]: ...
    def shorten_title(self, title: str, max_length: int = ...) -> str: ...
    def upload_video_to_youtube(
        self,
        video_file: str,
        youtube_title: str,
        youtube_description: str,
    ) -> str: ...
    def process(self) -> dict[str, str]: ...

class YouTubeChannelManager:
    youtube: YouTubeAuth
    logger: Logger
    def __init__(
        self,
        youtube_client: YouTubeAuth,
        logger: Logger | None = ...,
    ) -> None: ...
    def list_channel(self) -> Generator[dict[str, str]] | None: ...
    def get_video_details(self, video_ids: list[str]) -> Generator[dict[str, str]]: ...
    @staticmethod
    def filter_pending_videos(videos: Iterable[dict[str, str]]) -> list[dict[str, str]]: ...
    def delete_video(self, video_id: str) -> bool: ...