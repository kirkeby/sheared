# vim:nowrap:textwidth=0
import stackless
import sys

class CoroutineReturned(Exception):
    pass
class CoroutineFailed(Exception):
    pass

def bootstrapCoroutine(coroutine, f):
    tasklet_coroutines[id(coroutine.tasklet)] = coroutine
    #creator = tasklet_coroutines[id(stackless.getcurrent())]

    coroutine.tasklet.become()
    args, kwargs = coroutine.channel.receive()
    creator = coroutine.caller
    try:
        try:
            coroutine.result = apply(f, args, kwargs)
            creator.channel.send_exception(CoroutineReturned, coroutine)
            #coroutine.caller.channel.send_exception(CoroutineReturned, coroutine)
        except CoroutineReturned, ex:
            creator.channel.send_exception(CoroutineReturned, ex[0])
        except CoroutineFailed, ex:
            creator.channel.send_exception(CoroutineFailed, ex[0])
        except:
            coroutine.exc_info = sys.exc_info()
            creator.channel.send_exception(CoroutineFailed, coroutine)
            #coroutine.caller.channel.send_exception(CoroutineFailed, coroutine, e)

#        try:
#            apply(f, args, kwargs)
#            creator.channel.send_exception(CoroutineReturned, coroutine)
#        except CoroutineReturned, c:
#            raise
#        except:
#            coroutine.exc_info = sys.exc_info()
#            raise CoroutineFailed, coroutine
    finally:
        del tasklet_coroutines[id(coroutine.tasklet)]

tasklet_coroutines = {}
class Coroutine:
    def __init__(self, f, name='foo'):
        self.name = name
        self.tasklet = stackless.tasklet()
        self.channel = stackless.channel()
        bootstrapCoroutine(self, f).run()

    def __call__(self, *args, **kwargs):
        caller = self.caller = tasklet_coroutines[id(stackless.getcurrent())]
        self.channel.send((args, kwargs))
        args, kwargs = caller.channel.receive()

        # this is a kludge to allow kwargs to be passed when
        # we first invoke the coroutine,
        if kwargs:
            raise TypeError, 'can onlt pass **kwargs to first invocation of coroutine'
        # *args turn f() into (), f(1) into (1,) and f(1, 2) into (1,2).  for coroutines
        # to "return" values as normal functions do, we go through these hoops,
        if len(args) == 0:
            return
        if len(args) == 1:
            return args[0]
        else:
            return args

class FIFO:
    def __init__(self):
        self.channel = stackless.channel()
    def take(self):
        args = self.channel.receive()
        # see last comment in Coroutine.__call__,
        if len(args) == 0:
            return
        if len(args) == 1:
            return args[0]
        else:
            return args
    def give(self, *args):
        self.channel.send(args)

def init():
    class DummyCoroutine:
        def __init__(self):
            self.tasklet = stackless.getcurrent()
            self.channel = stackless.channel()
    dummy = DummyCoroutine()
    tasklet_coroutines[id(dummy.tasklet)] = dummy
init()

__all__ = ['Coroutine', 'CoroutineFailed', 'CoroutineReturned', 'init']
