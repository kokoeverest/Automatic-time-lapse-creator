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
