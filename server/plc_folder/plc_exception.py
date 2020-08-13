class ParametersError(Exception):
    """for the parameters are not correct"""

    def __init__(self, message):
        super().__init__(message)


class PLCConnectionError(Exception):
    """for the connection is not successful"""

    def __init__(self, message):
        super().__init__(message)


class NewError(Exception):
    """For new variable's error if it does not exist in database"""

    def __init__(self, message):
        super().__init__(message)


class CurrentError(Exception):
    """For the current data error"""

    def __init__(self, message):
        super().__init__(message)


class OldDataError(Exception):
    """For the old data error"""

    def __init__(self, message):
        super().__init__(message)


class WriteError(Exception):
    """For write function"""

    def __init__(self, message):
        super().__init__(message)


class DatablockSizeError(Exception):
    """For datablock size error."""

    def __init__(self, message):
        super().__init__(message)


class MissingConnection(Exception):
    """For missing connection"""

    def __init__(self, message):
        super().__init__(message)


class InitializeError(Exception):
    """For incorrect initialize"""

    def __init__(self, message):
        super().__init__(message)


class DatabaseError(Exception):
    """For incorrect database format"""

    def __init__(self, message):
        super().__init__(message)

