import os


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
    if os.path.isdir(path):
        start_idx = 2
    else:
        start_idx = 3

    head, tail = os.path.split(path)
    head = sep.join(head.split(sep)[-start_idx:])
    return f"{head}{sep}{tail}"
