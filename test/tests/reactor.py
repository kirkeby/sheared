# First line.
# vim:nowrap:textwidth=0

import unittest
import socket, os, time, errno, commands, random

from sheared.reactor import selectable
from sheared.python import coroutine

class ReactorTestCase(unittest.TestCase):
    """Test a reactor."""

    def setUp(self):
        self.reactor.reset()

    def testCanReset(self):
        """Test that the reactor can be reset."""
        self.reactor.run()
        self.reactor.reset()
        self.reactor.run()

    def testNothingToDo(self):
        """Test that the reactor cleanly exits when there is nothing to do."""
        self.reactor.run()

    def singleCoroutineRun(self, f):
        try:
            co = coroutine.Coroutine(f)
            self.reactor.addCoroutine(co, (self.reactor,))
            self.reactor.run()
            return getattr(self.reactor, 'result', None)
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]

    def testRead(self):
        """Test reading from an open file."""
        def f(reactor):
            fd = os.open('test/tests/reactor.py', os.O_RDONLY)
            fd = reactor.prepareFile(fd)
            lines = reactor.read(fd, 4096).split('\n')
            self.assertEquals(lines[0], '# First line.')
        self.singleCoroutineRun(f)
        
    def testBadWrite(self):
        """Test that the reactor works given bad input to write."""
        def f(reactor):
            f = reactor.open('/dev/null', 'w')
            try:
                reactor.write(f, None)
                reactor.shutdown('None')
            except TypeError:
                pass
            reactor.shutdown('ok')
        self.assertEquals(self.singleCoroutineRun(f), 'ok')

    def testImmediateStop(self):
        """Test that the reactor cleanly exits upon an immediate shutdown-command."""
        def f(reactor):
            reactor.shutdown(42)
        try:
            co = coroutine.Coroutine(f)
            self.reactor.addCoroutine(co, (self.reactor,))
            self.reactor.run()
            self.assertEquals(self.reactor.result, 42, "return value is wrong")
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]
        
    def testDelayedStop(self):
        """Test that the reactor cleanly exits upon delayed shutdown-command."""
        def f(reactor):
            started = time.time()
            reactor.sleep(0.5)
            stopped = time.time()
            assert stopped - started >= 0.45
            reactor.shutdown(42)
        try:
            co = coroutine.Coroutine(f)
            self.reactor.addCoroutine(co, (self.reactor,))
            self.reactor.run()
            self.assertEquals(self.reactor.result, 42, "return value is wrong")
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]

    def testRefusedConnection(self):
        def g(reactor, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock = reactor.prepareFile(sock)
            try:
                reactor.connect(sock, ('127.0.0.1', port))
                reactor.shutdown(0)
            except socket.error, (err, mesg):
                if not err == errno.ECONNREFUSED:
                    raise
                reactor.shutdown(42)

        def h(reactor):
            reactor.sleep(1.0)
            reactor.shutdown(1)

        try:
            port = random.random() * 8192 + 22000
            self.reactor.addCoroutine(coroutine.Coroutine(g), (self.reactor, port))
            self.reactor.addCoroutine(coroutine.Coroutine(h), (self.reactor,))
            self.reactor.run()
            self.failUnless(hasattr(self.reactor, 'result'), 'return value missing')
            self.assertEqual(self.reactor.result, 42)
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]

    def testSimplePair(self):
        """Test that the reactor works with a simple TCP client / server."""
        def f(reactor, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.listen(1)
            sock = reactor.prepareFile(sock)
            fd, addr = reactor.accept(sock)
            reactor.close(sock)
            d = reactor.read(fd, 4096)
            reactor.shutdown(d)
            fd.close()

        def g(reactor, port):
            reactor.sleep(1)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock = reactor.prepareFile(sock)
            reactor.connect(sock, ('127.0.0.1', port))
            reactor.write(sock, 'Hello, World\n')
            reactor.close(sock)

        try:
            port = random.random() * 8192 + 22000
            self.reactor.addCoroutine(coroutine.Coroutine(f, 'server'), (self.reactor, port))
            self.reactor.addCoroutine(coroutine.Coroutine(g, 'client'), (self.reactor, port))
            self.reactor.run()
            self.failUnless(hasattr(self.reactor, 'result'), 'return value missing')
            self.assertEqual(self.reactor.result, "Hello, World\n", "return value is wrong")
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]

    def testSimpleServer(self):
        """Test that the reactor works with a simple TCP server."""
        def f(reactor, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.listen(1)
            sock = reactor.prepareFile(sock)
            fd, addr = reactor.accept(sock)
            reactor.close(sock)
            d = reactor.read(fd, 4096)
            fd.close()
            return d

        def g(reactor, port):
            os.system('( echo "Hello, World" | ./bin/netcat localhost %d ) &' % port)
            reactor.sleep(2.0)
            reactor.shutdown(42)

        try:
            port = random.random() * 8192 + 22000
            co = coroutine.Coroutine(f)
            self.reactor.addCoroutine(co, (self.reactor, port))
            self.reactor.addCoroutine(coroutine.Coroutine(g), (self.reactor, port))
            self.reactor.run()
            self.failUnless(hasattr(co, 'result'), 'return value missing')
            self.assertEqual(co.result, "Hello, World\n", "return value is wrong")
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]

    def testTransport(self):
        """Test that the reactor can working Transports."""
        def read(reactor, file, count):
            t = reactor.createTransport(os.open(file, os.O_RDONLY), 'file://' + file)
            v = t.read(count)
            t.close()
            return v
        def write(reactor, file, data):
            t = reactor.createTransport(os.open(file, os.O_WRONLY), 'file://' + file)
            t.write(data)
            t.close()
            return 1

        readZero = coroutine.Coroutine(read)
        readPasswd = coroutine.Coroutine(read)
        writeNull = coroutine.Coroutine(write)
        self.reactor.addCoroutine(readZero, (self.reactor, '/dev/zero', 1024))
        self.reactor.addCoroutine(readPasswd, (self.reactor, '/etc/passwd', 1024))
        self.reactor.addCoroutine(writeNull, (self.reactor, '/dev/null', 'Hello, World!'))
        self.reactor.run()

        self.assertEqual(readZero.result, '\0' * 1024)
        self.failUnless(len(readPasswd.result))
        self.assertEqual(writeNull.result, 1)
            
class SelectableReactorTestCase(ReactorTestCase):
    """Test-cases for the selectable reactor."""
    reactor = selectable

suite = unittest.makeSuite(SelectableReactorTestCase, 'test')

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
