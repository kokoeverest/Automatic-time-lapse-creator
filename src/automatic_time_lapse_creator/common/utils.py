import os
from .constants import (
    DEFAULT_VIDEO_DESCRIPTION,
    MONTHLY_SUMMARY_VIDEO_DESCRIPTION,
    MONTH_NAMES,
)


def create_log_message(location: str, url: str, method: str) -> str:
    """
    Creates an appropriate log message according to the method which calls it

    Returns::

        str - the log message if the method is 'add' or 'remove'"""
    if method == "add":
        return f"Source with location: {location} or url: {url} already exists!"
    elif method == "remove":
        return f"Source with location: {location} or url: {url} doesn't exist!"
    else:
        return f"Unknown command: {method}"


def shorten(path: str) -> str:
    """
    Receives a file path and trims the first part returning a more readable,
    short version of it

    Returns::

        str - the shortened path
    """
    sep = os.path.sep
    start_idx = 2 if os.path.isdir(path) else 3

    head, tail = os.path.split(path)
    head = sep.join(head.split(sep)[-start_idx:])
    return f"{head}{sep}{tail}"


def dash_sep_strings(*args: str):
    """Create a dash separated string from many strings in the format:
    "str1-str2-str3" etc.
    """
    return "-".join(args)


def create_description_for_monthly_video(monthly_video: str):
    """Creates a comprehensive description for the monthly summary videos.

    Args::
        monthly_video: str - the video path of the monthly video

    Returns::
        str - the created description
    """
    _, tail = os.path.split(monthly_video)
    year = tail[:4]
    month = tail[5:7]
    month_name = MONTH_NAMES[int(month)]
    suffix = f"{month_name}, {year}"

    result = f"{MONTHLY_SUMMARY_VIDEO_DESCRIPTION}{suffix}\n{DEFAULT_VIDEO_DESCRIPTION}"
    return result


def video_type_response(video_path: str, video_type: str) -> dict[str, str]:
    """Returns a response dict containing the video path and the video_type eg. "daily" or "monthly"
    so the queue can distinguish between the two.

    Returns::

        dict[str, str] - the response dictionary
    """
    return {"video_path": video_path, "video_type": video_type}
