from __future__ import annotations

import logging
import os
import smtplib
from queue import Empty
from unittest.mock import MagicMock, call, mock_open, patch

import pytest
import tests.test_data as td
from src.automatic_time_lapse_creator.youtube_manager import YouTubeAuth
from src.automatic_time_lapse_creator.common.constants import (
    AuthMethod,
    DEFAULT_EMAIL_AUTH_TIMEOUT_SECONDS,
)


@pytest.fixture
def mock_logger():
    mock_logger = MagicMock(spec=logging.Logger)
    yield mock_logger
    mock_logger.reset_mock()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_youtube_auth(
    auth_method: AuthMethod = AuthMethod.MANUAL,
    redirect_url: str | None = None,
    email_auth_timeout_seconds: int = DEFAULT_EMAIL_AUTH_TIMEOUT_SECONDS,
) -> YouTubeAuth:
    """Instantiate YouTubeAuth with all external I/O patched out."""
    mock_credentials = MagicMock(valid=True, expired=False)
    with (
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Credentials.from_authorized_user_file",
            return_value=mock_credentials,
        ),
        patch("os.path.exists", return_value=True),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.build",
            return_value=MagicMock(),
        ),
    ):
        return YouTubeAuth(
            td.mock_secrets_file,
            auth_method=auth_method,
            redirect_url=redirect_url,
            email_auth_timeout_seconds=email_auth_timeout_seconds,
        )


def _make_email_auth_mocks(redirect: str = "http://localhost:8080"):
    """Return (mock_flow, mock_process, mock_queue, mock_creds) for email auth tests."""
    mock_creds = MagicMock()
    mock_flow = MagicMock()
    mock_flow.authorization_url.return_value = ("http://auth.url/login", {})

    mock_process = MagicMock()
    mock_process.is_alive.return_value = False

    # Do not use spec=Queue here: multiprocessing.Queue methods are C-level and
    # won't appear in the spec, making .get inaccessible on the mock.
    mock_queue = MagicMock()
    mock_queue.get.return_value = mock_creds

    return mock_flow, mock_process, mock_queue, mock_creds


# ---------------------------------------------------------------------------
# validate_secrets_file
# ---------------------------------------------------------------------------

def test_validate_secrets_file_valid(mock_logger: MagicMock):
    # Arrange, Act & Assert
    with (
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        patch("os.path.isfile", return_value=True),
    ):
        assert not YouTubeAuth.validate_secrets_file(mock_logger, td.mock_secrets_file)


def test_validate_secrets_file_invalid_json(mock_logger: MagicMock):
    # Arrange, Act & Assert
    with (
        patch("builtins.open", mock_open(read_data=td.invalid_json_content)),
        patch("os.path.isfile", return_value=True),
    ):
        with pytest.raises(Exception):
            YouTubeAuth.validate_secrets_file(mock_logger, td.mock_secrets_file)


def test_validate_secrets_file_missing_file(mock_logger: MagicMock):
    # Arrange, Act & Assert
    with patch("os.path.isfile", return_value=False):
        with pytest.raises(FileNotFoundError):
            YouTubeAuth.validate_secrets_file(mock_logger, td.mock_secrets_file)


# ---------------------------------------------------------------------------
# authenticate_youtube
# ---------------------------------------------------------------------------

def test_authenticate_youtube_with_valid_token(mock_logger: MagicMock):
    # Arrange
    mock_credentials = MagicMock(valid=True, expired=False)
    with (
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        patch("os.path.exists", return_value=True),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Credentials.from_authorized_user_file",
            return_value=mock_credentials,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.build",
            return_value="YouTubeService",
        ),
    ):
        youtube_instance = YouTubeAuth(td.mock_secrets_file)

        # Act
        result = youtube_instance.authenticate_youtube(td.mock_secrets_file)

    # Assert
    assert result == "YouTubeService"


def test_authenticate_youtube_with_new_auth(mock_logger: MagicMock):
    # Arrange
    mock_credentials = MagicMock()
    mock_credentials.to_json.return_value = '{"token": "new"}'
    with (
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        patch("os.path.exists", return_value=False),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.YouTubeAuth.open_browser_to_authenticate",
            return_value=mock_credentials,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.build",
            return_value="YouTubeService",
        ),
    ):
        youtube_instance = YouTubeAuth(td.mock_secrets_file)

        # Act
        result = youtube_instance.authenticate_youtube(td.mock_secrets_file)

    # Assert
    assert result == "YouTubeService"


def test_authenticate_youtube_refreshes_expired_token():
    # Arrange
    mock_credentials = MagicMock(valid=False, expired=True, refresh_token="refresh_tok")
    mock_credentials.refresh.side_effect = None
    mock_credentials.valid = True
    with (
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        patch("os.path.exists", return_value=True),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Credentials.from_authorized_user_file",
            return_value=mock_credentials,
        ),
        patch("src.automatic_time_lapse_creator.youtube_manager.Request"),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.build",
            return_value="YouTubeService",
        ),
    ):
        youtube_instance = YouTubeAuth(td.mock_secrets_file)

        # Act
        result = youtube_instance.authenticate_youtube(td.mock_secrets_file)

    # Assert
    assert result == "YouTubeService"


def test_authenticate_youtube_re_authenticates_when_refresh_fails():
    # Arrange
    mock_credentials = MagicMock(valid=False, expired=True, refresh_token="tok")
    mock_credentials.refresh.side_effect = Exception("token revoked")
    mock_new_credentials = MagicMock()
    mock_new_credentials.to_json.return_value = '{"token": "refreshed"}'

    with (
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        patch("os.path.exists", return_value=True),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Credentials.from_authorized_user_file",
            return_value=mock_credentials,
        ),
        patch("src.automatic_time_lapse_creator.youtube_manager.Request"),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.YouTubeAuth.open_browser_to_authenticate",
            return_value=mock_new_credentials,
        ) as mock_browser_auth,
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.build",
            return_value="YouTubeService",
        ),
    ):
        youtube_instance = YouTubeAuth(td.mock_secrets_file)

        # Act
        youtube_instance.authenticate_youtube(td.mock_secrets_file)

    # Assert
    mock_browser_auth.assert_called()


def test_authenticate_youtube_with_corrupted_token_falls_back_to_reauthentication():
    # Arrange
    mock_new_credentials = MagicMock()
    mock_new_credentials.to_json.return_value = '{"token": "new"}'

    with (
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        patch("os.path.exists", return_value=True),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Credentials.from_authorized_user_file",
            side_effect=ValueError("corrupted token file"),
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.YouTubeAuth.open_browser_to_authenticate",
            return_value=mock_new_credentials,
        ) as mock_browser_auth,
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.build",
            return_value="YouTubeService",
        ),
    ):
        youtube_instance = YouTubeAuth(td.mock_secrets_file)

        # Act
        result = youtube_instance.authenticate_youtube(td.mock_secrets_file)

    # Assert
    assert result == "YouTubeService"
    mock_browser_auth.assert_called()


# ---------------------------------------------------------------------------
# __init__ – redirect_url / auth_method validation
# ---------------------------------------------------------------------------

def test_init_raises_value_error_when_email_method_without_redirect_url():
    # Arrange & Act & Assert
    with (
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open(read_data=td.valid_json_content)),
        pytest.raises(ValueError, match="redirect_url required for EMAIL auth."),
    ):
        YouTubeAuth(td.mock_secrets_file, auth_method=AuthMethod.EMAIL, redirect_url=None)


def test_init_sets_redirect_url_for_email_method():
    # Arrange
    redirect = "http://localhost:8080"

    # Act
    instance = _make_youtube_auth(auth_method=AuthMethod.EMAIL, redirect_url=redirect)

    # Assert
    assert instance.redirect_url == redirect
    assert instance.auth_method == AuthMethod.EMAIL


def test_init_sets_redirect_url_to_none_for_manual_method():
    # Act
    instance = _make_youtube_auth(auth_method=AuthMethod.MANUAL)

    # Assert
    assert instance.redirect_url is None
    assert instance.auth_method == AuthMethod.MANUAL


def test_init_stores_custom_email_auth_timeout():
    # Arrange
    timeout = 120

    # Act
    instance = _make_youtube_auth(
        auth_method=AuthMethod.EMAIL,
        redirect_url="http://localhost:8080",
        email_auth_timeout_seconds=timeout,
    )

    # Assert
    assert instance.email_auth_timeout_seconds == timeout


def test_init_stores_default_email_auth_timeout_for_manual():
    # Act
    instance = _make_youtube_auth(auth_method=AuthMethod.MANUAL)

    # Assert
    assert instance.email_auth_timeout_seconds == DEFAULT_EMAIL_AUTH_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# open_browser_to_authenticate – MANUAL branch
# ---------------------------------------------------------------------------

def test_open_browser_to_authenticate_uses_run_local_server_for_manual():
    # Arrange
    instance = _make_youtube_auth(auth_method=AuthMethod.MANUAL)
    mock_flow = MagicMock()
    mock_creds = MagicMock()
    mock_flow.run_local_server.return_value = mock_creds

    with patch(
        "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
        return_value=mock_flow,
    ):
        # Act
        result = instance.open_browser_to_authenticate(td.mock_secrets_file)

    # Assert
    mock_flow.run_local_server.assert_called_once_with(port=0)
    assert result is mock_creds


def test_open_browser_to_authenticate_manual_wraps_exception_in_runtime_error():
    # Arrange
    instance = _make_youtube_auth(auth_method=AuthMethod.MANUAL)

    # Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            side_effect=Exception("flow failed"),
        ),
        pytest.raises(RuntimeError, match="YouTube Authentication failed"),
    ):
        instance.open_browser_to_authenticate(td.mock_secrets_file)


def test_open_browser_to_authenticate_manual_does_not_send_email_on_error():
    # Arrange
    instance = _make_youtube_auth(auth_method=AuthMethod.MANUAL)

    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            side_effect=Exception("flow failed"),
        ),
        patch.object(YouTubeAuth, "notify_by_email") as mock_notify,
        # Act & Assert
        pytest.raises(RuntimeError),
    ):
        instance.open_browser_to_authenticate(td.mock_secrets_file)

    # Assert
    mock_notify.assert_not_called()


# ---------------------------------------------------------------------------
# open_browser_to_authenticate – EMAIL branch
# ---------------------------------------------------------------------------

def test_open_browser_to_authenticate_email_sets_redirect_uri_and_sends_email():
    # Arrange
    redirect = "http://localhost:9090"
    instance = _make_youtube_auth(auth_method=AuthMethod.EMAIL, redirect_url=redirect)
    mock_flow, mock_process, mock_queue, mock_creds = _make_email_auth_mocks(redirect)

    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Process",
            return_value=mock_process,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Queue",
            return_value=mock_queue,
        ),
        patch.object(YouTubeAuth, "notify_by_email") as mock_notify,
    ):
        # Act
        result = instance.open_browser_to_authenticate(td.mock_secrets_file)

    # Assert
    assert mock_flow.redirect_uri == redirect
    mock_flow.authorization_url.assert_called_once_with(prompt="consent")
    mock_notify.assert_called_once_with(
        logger=instance.logger, auth_url="http://auth.url/login"
    )
    mock_process.start.assert_called_once()
    mock_process.join.assert_called_once_with(timeout=instance.email_auth_timeout_seconds)
    assert result is mock_creds


def test_open_browser_to_authenticate_email_uses_port_from_redirect_url():
    # Arrange
    redirect = "http://myserver.com:12345/callback"
    instance = _make_youtube_auth(auth_method=AuthMethod.EMAIL, redirect_url=redirect)
    mock_flow, mock_process, mock_queue, _ = _make_email_auth_mocks(redirect)

    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Process",
            return_value=mock_process,
        ) as mock_process_cls,
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Queue",
            return_value=mock_queue,
        ),
        patch.object(YouTubeAuth, "notify_by_email"),
    ):
        # Act
        instance.open_browser_to_authenticate(td.mock_secrets_file)

    # Assert – _auth_worker args: (flow, host, port, queue)
    spawned_args = mock_process_cls.call_args.kwargs["args"]
    assert spawned_args[1] == "0.0.0.0"
    assert spawned_args[2] == 12345


def test_open_browser_to_authenticate_email_uses_default_port_8080_when_no_port_in_url():
    # Arrange
    redirect = "http://myserver.com/callback"
    instance = _make_youtube_auth(auth_method=AuthMethod.EMAIL, redirect_url=redirect)
    mock_flow, mock_process, mock_queue, _ = _make_email_auth_mocks(redirect)

    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Process",
            return_value=mock_process,
        ) as mock_process_cls,
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Queue",
            return_value=mock_queue,
        ),
        patch.object(YouTubeAuth, "notify_by_email"),
    ):
        # Act
        instance.open_browser_to_authenticate(td.mock_secrets_file)

    # Assert
    spawned_args = mock_process_cls.call_args.kwargs["args"]
    assert spawned_args[2] == 8080


def test_open_browser_to_authenticate_email_raises_on_timeout():
    # Arrange
    redirect = "http://localhost:8080"
    instance = _make_youtube_auth(
        auth_method=AuthMethod.EMAIL,
        redirect_url=redirect,
        email_auth_timeout_seconds=30,
    )
    mock_flow, mock_process, mock_queue, _ = _make_email_auth_mocks(redirect)
    mock_process.is_alive.return_value = True  # still alive → timed out

    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Process",
            return_value=mock_process,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Queue",
            return_value=mock_queue,
        ),
        patch.object(YouTubeAuth, "notify_by_email"),
        # Act & Assert – original RuntimeError re-raised without double-wrapping
        pytest.raises(RuntimeError, match="User authentication timed out."),
    ):
        instance.open_browser_to_authenticate(td.mock_secrets_file)

    # Assert
    mock_process.terminate.assert_called_once()
    # join called twice: main join + zombie-reaping join after terminate
    assert mock_process.join.call_args_list == [
        call(timeout=30),
        call(timeout=5),
    ]


def test_open_browser_to_authenticate_email_sends_failure_email_on_error():
    # Arrange
    redirect = "http://localhost:8080"
    instance = _make_youtube_auth(auth_method=AuthMethod.EMAIL, redirect_url=redirect)

    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            side_effect=Exception("unexpected error"),
        ),
        patch.object(YouTubeAuth, "notify_by_email") as mock_notify,
        # Act & Assert
        pytest.raises(RuntimeError, match="YouTube Authentication failed"),
    ):
        instance.open_browser_to_authenticate(td.mock_secrets_file)

    # Assert – only one email sent: the failure notification (flow creation failed
    # before the auth_url notification could be made)
    mock_notify.assert_called_once()
    _, call_kwargs = mock_notify.call_args
    assert "message" in call_kwargs


def test_open_browser_to_authenticate_email_sends_auth_url_then_failure_email_on_process_error():
    """notify_by_email is called twice: once for auth URL, once for the error."""
    # Arrange
    redirect = "http://localhost:8080"
    instance = _make_youtube_auth(auth_method=AuthMethod.EMAIL, redirect_url=redirect)
    mock_flow, _, _, _ = _make_email_auth_mocks(redirect)

    mock_process = MagicMock()
    mock_process.is_alive.return_value = True  # timeout!
    mock_queue = MagicMock()

    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Process",
            return_value=mock_process,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Queue",
            return_value=mock_queue,
        ),
        patch.object(YouTubeAuth, "notify_by_email") as mock_notify,
        # Act & Assert
        pytest.raises(RuntimeError),
    ):
        instance.open_browser_to_authenticate(td.mock_secrets_file)

    # Assert
    assert mock_notify.call_count == 2
    first_call_kwargs = mock_notify.call_args_list[0][1]
    assert "auth_url" in first_call_kwargs
    second_call_kwargs = mock_notify.call_args_list[1][1]
    assert "message" in second_call_kwargs


def test_open_browser_to_authenticate_email_re_raises_exception_from_queue():
    # Arrange
    redirect = "http://localhost:8080"
    instance = _make_youtube_auth(auth_method=AuthMethod.EMAIL, redirect_url=redirect)
    mock_flow, mock_process, mock_queue, _ = _make_email_auth_mocks(redirect)
    mock_queue.get.return_value = ValueError("auth worker crashed")

    # Act & Assert
    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Process",
            return_value=mock_process,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Queue",
            return_value=mock_queue,
        ),
        patch.object(YouTubeAuth, "notify_by_email"),
        pytest.raises(RuntimeError, match="YouTube Authentication failed"),
    ):
        instance.open_browser_to_authenticate(td.mock_secrets_file)


def test_open_browser_to_authenticate_email_raises_when_queue_is_empty_after_worker_crash():
    # Arrange
    redirect = "http://localhost:8080"
    instance = _make_youtube_auth(auth_method=AuthMethod.EMAIL, redirect_url=redirect)
    mock_flow, mock_process, _, _ = _make_email_auth_mocks(redirect)

    mock_queue = MagicMock()
    mock_queue.get.side_effect = Empty  # worker exited without writing to the queue

    # Act & Assert – original RuntimeError re-raised without double-wrapping
    with (
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Process",
            return_value=mock_process,
        ),
        patch(
            "src.automatic_time_lapse_creator.youtube_manager.Queue",
            return_value=mock_queue,
        ),
        patch.object(YouTubeAuth, "notify_by_email"),
        pytest.raises(RuntimeError, match="Worker process exited without returning credentials."),
    ):
        instance.open_browser_to_authenticate(td.mock_secrets_file)


# ---------------------------------------------------------------------------
# _auth_worker
# ---------------------------------------------------------------------------

def test_auth_worker_puts_credentials_in_queue():
    # Use queue.Queue (threading-based) to avoid multiprocessing pickling of MagicMock
    from queue import Queue as ThreadQueue

    # Arrange
    mock_flow = MagicMock()
    mock_creds = MagicMock()
    mock_flow.run_local_server.return_value = mock_creds
    q = ThreadQueue()

    # Act
    YouTubeAuth._auth_worker(mock_flow, "0.0.0.0", 8080, q)

    # Assert
    result = q.get(timeout=1)
    assert result is mock_creds
    mock_flow.run_local_server.assert_called_once_with(
        host="0.0.0.0",
        port=8080,
        open_browser=False,
        authorization_prompt_message="Authorize here: {url}",
        success_message="Success! You can close this tab.",
    )


def test_auth_worker_puts_exception_in_queue_on_failure():
    from queue import Queue as ThreadQueue

    # Arrange
    mock_flow = MagicMock()
    error = RuntimeError("server crashed")
    mock_flow.run_local_server.side_effect = error
    q = ThreadQueue()

    # Act
    YouTubeAuth._auth_worker(mock_flow, "0.0.0.0", 8080, q)

    # Assert
    result = q.get(timeout=1)
    assert isinstance(result, RuntimeError)
    assert str(result) == "server crashed"


# ---------------------------------------------------------------------------
# notify_by_email
# ---------------------------------------------------------------------------

def test_notify_by_email_logs_error_when_env_vars_missing(mock_logger: MagicMock):
    # Arrange & Act
    with patch.dict(os.environ, {}, clear=True):
        YouTubeAuth.notify_by_email(logger=mock_logger, auth_url="http://auth.url")

    # Assert
    mock_logger.error.assert_called_once()


def test_notify_by_email_logs_error_when_only_some_env_vars_missing(mock_logger: MagicMock):
    # Arrange
    partial_env = {
        "EMAIL_SENDER": "sender@example.com",
        # missing EMAIL_RECEIVER, SMTP_SERVER, etc.
    }

    # Act
    with patch.dict(os.environ, partial_env, clear=True):
        YouTubeAuth.notify_by_email(logger=mock_logger, auth_url="http://auth.url")

    # Assert
    mock_logger.error.assert_called_once()


def test_notify_by_email_sends_auth_url_email_successfully(mock_logger: MagicMock):
    # Arrange
    env = {
        "EMAIL_SENDER": "sender@example.com",
        "EMAIL_RECEIVER": "receiver@example.com",
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    }
    mock_smtp_instance = MagicMock()

    with (
        patch.dict(os.environ, env),
        patch("smtplib.SMTP") as mock_smtp_cls,
    ):
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp_instance
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Act
        YouTubeAuth.notify_by_email(logger=mock_logger, auth_url="http://auth.url/login")

    # Assert
    mock_logger.info.assert_called_once()
    mock_logger.error.assert_not_called()


def test_notify_by_email_sends_error_message_email_successfully(mock_logger: MagicMock):
    # Arrange
    env = {
        "EMAIL_SENDER": "sender@example.com",
        "EMAIL_RECEIVER": "receiver@example.com",
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    }
    mock_smtp_instance = MagicMock()

    with (
        patch.dict(os.environ, env),
        patch("smtplib.SMTP") as mock_smtp_cls,
    ):
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp_instance
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Act
        YouTubeAuth.notify_by_email(logger=mock_logger, message="Something went wrong")

    # Assert
    mock_logger.info.assert_called_once()
    mock_logger.error.assert_not_called()


def test_notify_by_email_uses_auth_url_in_body_when_provided(mock_logger: MagicMock):
    # Arrange
    env = {
        "EMAIL_SENDER": "sender@example.com",
        "EMAIL_RECEIVER": "receiver@example.com",
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    }
    captured_messages: list[str] = []

    def capture_sendmail(sender, receiver, raw_msg):
        captured_messages.append(raw_msg)

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.sendmail.side_effect = capture_sendmail

    with (
        patch.dict(os.environ, env),
        patch("smtplib.SMTP") as mock_smtp_cls,
    ):
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp_instance
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Act
        YouTubeAuth.notify_by_email(logger=mock_logger, auth_url="http://auth.url/login")

    # Assert
    assert len(captured_messages) == 1
    assert "http://auth.url/login" in captured_messages[0]


def test_notify_by_email_uses_message_as_body_when_provided(mock_logger: MagicMock):
    # Arrange
    env = {
        "EMAIL_SENDER": "sender@example.com",
        "EMAIL_RECEIVER": "receiver@example.com",
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    }
    captured_messages: list[str] = []

    def capture_sendmail(sender, receiver, raw_msg):
        captured_messages.append(raw_msg)

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.sendmail.side_effect = capture_sendmail

    with (
        patch.dict(os.environ, env),
        patch("smtplib.SMTP") as mock_smtp_cls,
    ):
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp_instance
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Act
        YouTubeAuth.notify_by_email(logger=mock_logger, message="Auth failed: timeout")

    # Assert
    assert len(captured_messages) == 1
    assert "Auth failed: timeout" in captured_messages[0]


def test_notify_by_email_logs_error_on_smtp_failure(mock_logger: MagicMock):
    # Arrange
    env = {
        "EMAIL_SENDER": "sender@example.com",
        "EMAIL_RECEIVER": "receiver@example.com",
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    }

    # Act
    with (
        patch.dict(os.environ, env),
        patch("smtplib.SMTP", side_effect=smtplib.SMTPException("connection refused")),
    ):
        YouTubeAuth.notify_by_email(logger=mock_logger, auth_url="http://auth.url")

    # Assert
    mock_logger.error.assert_called_once()
    mock_logger.info.assert_not_called()


def test_notify_by_email_logs_error_and_defaults_port_when_smtp_port_is_invalid(
    mock_logger: MagicMock,
):
    # Arrange
    env = {
        "EMAIL_SENDER": "sender@example.com",
        "EMAIL_RECEIVER": "receiver@example.com",
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "not_a_number",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    }
    mock_smtp_instance = MagicMock()

    with (
        patch.dict(os.environ, env),
        patch("smtplib.SMTP") as mock_smtp_cls,
    ):
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp_instance
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Act
        YouTubeAuth.notify_by_email(logger=mock_logger, auth_url="http://auth.url")

    # Assert – invalid port is logged, email is still dispatched with the 587 fallback
    mock_logger.error.assert_called_once()
    mock_logger.info.assert_called_once()
    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)
