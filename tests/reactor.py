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
        self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)
        self.reactor.reset()
        self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)

    def testNothingToDo(self):
        """Test that the reactor cleanly exits when there is nothing to do."""
        self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)

    def testImmediateStop(self):
        """Test that the reactor cleanly exits upon an immediate shutdown-command."""
        def f(reactor):
            reactor.shutdown(42)
        try:
            co = coroutine.Coroutine(f)
            self.reactor.addCoroutine(co, (self.reactor,))
            self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)
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
            self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)
            self.assertEquals(self.reactor.result, 42, "return value is wrong")
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]

    def testRefusedConnection(self):
        def g(reactor, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            reactor.prepareFile(sock)
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
            self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)
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
            reactor.prepareFile(sock)
            fd, addr = reactor.accept(sock)
            sock.close()
            d = reactor.read(fd, 4096)
            fd.close()
            return d

        def g(reactor, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            reactor.prepareFile(sock)
            reactor.connect(sock, ('127.0.0.1', port))
            reactor.write(sock, 'Hello, World\n')
            sock.close()

        def h(reactor):
            reactor.sleep(1.0)
            reactor.shutdown(42)

        try:
            port = random.random() * 8192 + 22000
            co = coroutine.Coroutine(f)
            self.reactor.addCoroutine(co, (self.reactor, port))
            self.reactor.addCoroutine(coroutine.Coroutine(g), (self.reactor, port))
            self.reactor.addCoroutine(coroutine.Coroutine(h), (self.reactor,))
            self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)
            self.failUnless(hasattr(co, 'result'), 'return value missing')
            self.assertEqual(co.result, "Hello, World\n", "return value is wrong")
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]

    def testSimpleServer(self):
        """Test that the reactor works with a simple TCP server."""
        def f(reactor, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.listen(1)
            reactor.prepareFile(sock)
            fd, addr = reactor.accept(sock)
            sock.close()
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
            self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)
            self.failUnless(hasattr(co, 'result'), 'return value missing')
            self.assertEqual(co.result, "Hello, World\n", "return value is wrong")
        except coroutine.CoroutineFailed, ex:
            raise ex[0].exc_info[0], ex[0].exc_info[1], ex[0].exc_info[2]

    def testTransport(self):
        """Test that the reactor can working Transports."""
        def read(reactor, file, count):
            t = reactor.createTransport(open(file, 'r'), 'file://' + file)
            v = t.read(count)
            t.close()
            return v
        def write(reactor, file, data):
            t = reactor.createTransport(open(file, 'w'), 'file://' + file)
            t.write(data)
            t.close()
            return 1

        readZero = coroutine.Coroutine(read)
        readPasswd = coroutine.Coroutine(read)
        writeNull = coroutine.Coroutine(write)
        self.reactor.addCoroutine(readZero, (self.reactor, '/dev/zero', 1024))
        self.reactor.addCoroutine(readPasswd, (self.reactor, '/etc/passwd', 1024))
        self.reactor.addCoroutine(writeNull, (self.reactor, '/dev/null', 'Hello, World!'))
        self.assertRaises(coroutine.CoroutineReturned, self.reactor.run)

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
