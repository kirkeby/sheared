class Error(StandardError):
    pass

class CursorEmpty(Error):
    pass

class InterfaceError(Error):
    pass

class DatabaseError(Error):
    pass
class OperationalError(DatabaseError):
    pass
class ProgrammingError(DatabaseError):
    pass
