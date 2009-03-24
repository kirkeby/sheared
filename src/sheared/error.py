class ReactorExit(Exception):
    '''I am raised in all tasklets, when the reactor is about to shut down.'''
    pass

class TimeoutError(Exception):
    '''I am raised to signal a user-specified timeout expired.'''
    pass
