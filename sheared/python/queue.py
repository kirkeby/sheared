"""Simpleminded implementation of min-queue."""

class MinQueue:
    def __init__(self):
        self.list = []
    
    def insert(self, key, value):
        for i in range(len(self.list)):
            if self.list[i][0] > key:
                break
        self.list.insert(i, (key, value))

    def minkey(self):
        assert not self.empty(), 'empty queue'
        return self.list[0][0]

    def getmin(self):
        return self.pop(0)

__all__ = ['MinQueue']
