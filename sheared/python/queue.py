"""Simpleminded implementation of min-queue."""

class MinQueue:
    def __init__(self):
        self.queued = []

    def minkey(self):
        return self.queued[0][0]

    def getmin(self):
        return self.queued.pop(0)[1]

    def insert(self, key, value):
        i = 0
        for i in range(len(self.queued)):
            if self.queued[i][0] > key:
                break
        self.queued.insert(i, (key, value))

    def empty(self):
        return len(self.queued) == 0

__all__ = ['MinQueue']
