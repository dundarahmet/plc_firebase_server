class SecurityKeyError(Exception):

    def __init__(self, message):
        super().__init__(message)


class ListenError(Exception):

    def __init__(self, message):
        super().__init__(message)


class ChildError(Exception):

    def __init__(self, message):
        super().__init__(message)
