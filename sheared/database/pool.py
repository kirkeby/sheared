class ConnectionPool:
    def __init__(self, factory, max=4):
        self.factory = factory
        self.max = max

        self.connected = []
        self.available = []

    def leaseConnection(self):
        if self.available:
            return self.available.pop()
        
        if len(self.connected) < self.max:
            conn = self.factory()
            self.connected.append()
            
