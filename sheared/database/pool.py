from sheared.python import coroutine

class DatabaseConnectionPool:
    def __init__(self, factory, max=4):
        self.factory = factory
        self.max = max

        self.connected = []
        self.available = []
        self.waiting = 0
        self.fifo = coroutine.FIFO()

    def leaseConnection(self):
        if self.available:
            conn = self.available.pop()
        
        elif len(self.connected) < self.max:
            conn = self.factory()
            self.connected.append(conn)

        else:
            self.waiting = self.waiting + 1
            conn = self.fifo.take()
            self.waiting = self.waiting - 1

        return conn

    def releaseConnection(self, conn):
        assert conn in self.connected
        assert not conn in self.available

        if self.waiting:
            self.fifo.give(conn)
        else:
            self.available.append(conn)

    def query(self, sql):
        conn = self.leaseConnection()
        try:
            return conn.query(sql)
        finally:
            self.releaseConnection(conn)
