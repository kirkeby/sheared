class Error(StandardError):
    pass

class InterfaceError(Error):
    pass

class DatabaseError(Error):
    pass
class OperationalError(DatabaseError):
    pass
class ProgrammingError(DatabaseError):
    pass
