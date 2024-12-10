class UnknownLocationException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidStatusCodeException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidCollectionException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)