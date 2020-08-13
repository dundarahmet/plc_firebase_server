class LostInternetConnection(Exception):

    def __init__(self, message):
        super().__init__(message)

class UnexpectedVariable(Exception):

    def __init__(self, message):
        super().__init__(message)

class DatabaseWrongDataForm(Exception):

    def __init__(self, message):
        super().__init__(message)