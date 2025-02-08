from logging import Logger
from typing import Any, Iterable
from google.auth.external_account_authorized_user import Credentials as Creds
from google.oauth2.credentials import Credentials

class YouTubeAuth:
    def __init__(self, youtube_client_secrets_file: str) -> None: ...
    @classmethod
    def validate_secrets_file(
        cls, logger: Logger, secrets_file: str | None
    ) -> None: ...
    @classmethod
    def authenticate_youtube(
        cls, logger: Logger, youtube_client_secrets_file: str
    ) -> Any: ...
    @classmethod
    def open_browser_to_authenticate(cls, secrets_file: str) -> Credentials | Creds: ...

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
    def get_channel_id(self) -> str | None: ...
    def shorten_title(self, title: str, max_length: int = ...) -> str: ...
    def upload_video_to_youtube(
        self,
        video_file: str,
        youtube_title: str,
        youtube_description: str,
    ) -> str: ...
    def process(self) -> dict[str, str]: ...