# vim:nowrap:textwidth=0

from socket import htons, htonl, ntohs, ntohl
import struct
import string
import array

from sheared.python import coroutine

from sheared.database import error
from sheared.database import dummy

class ProtocolError(error.OperationalError):
    pass

class IncompletePacket(Exception):
    pass

def parseBytes(l, s):
    if len(s) < l:
        raise IncompletePacket()
    return s[0:l], s[l:]

def formatInt16(i):
    return struct.pack('h', htons(i))

def parseInt16(s):
    l = struct.calcsize('h')
    if len(s) < l:
        raise IncompletePacket()
    return ntohs(struct.unpack('h', s[0:l])[0]), s[l:]

def formatInt32(i):
    return struct.pack('i', htonl(i))

def parseInt32(s):
    l = struct.calcsize('i')
    if len(s) < l:
        raise IncompletePacket()
    return ntohl(struct.unpack('i', s[0:l])[0]), s[l:]

def formatLimString(l, s):
    if len(s) < l:
        return s + '\0' * (l - len(s))
    else:
        return s[0:l]

def formatString(s):
    return s + '\0'

def parseString(s):
    l = string.find(s, '\0')
    if l < 0:
        raise IncompletePacket
    return s[0:l], s[l + 1:]


class StartupPacket:
    def __init__(self, user, database='', args='', tty=''):
        self.user = user
        self.database = database
        self.args = args
        self.tty = tty
    def send(self, transport):
        s  = formatInt32(296)         # packet length
        s += formatInt16(2)           # protocol version, major
        s += formatInt16(0)           # protocol version, minor
        s += formatLimString(64, self.database)
        s += formatLimString(32, self.user)
        s += formatLimString(64, self.args)
        s += formatLimString(64, '')  # unused
        s += formatLimString(64, self.tty)
        transport.write(s)

class TerminatePacket:
    def send(self, transport):
        transport.write('X')

class QueryPacket:
    def __init__(self, query):
        self.query = query

    def send(self, transport):
        transport.write('Q' + formatString(self.query))

class CursorResponsePacket:
    def __init__(self, name):
        self.name = name

class EmptyQueryResponsePacket:
    pass

class CompletedResponsePacket:
    def __init__(self, cmd):
        self.command = cmd

class AuthenticationPacket:
    def __init__(self, auth):
        self.authentication = auth

class BackendKeyDataPacket:
    def __init__(self, pid, key):
        self.process_id = pid
        self.key = key

class ReadyForQueryPacket:
    pass

class RowDescriptionPacket:
    def __init__(self, columns):
        self.columns = columns

class AsciiRowPacket:
    def __init__(self, columns):
        self.columns = columns

class ErrorPacket:
    def __init__(self, message):
        self.message = message

class NoticeResponsePacket:
    def __init__(self, message):
        self.message = message

class UnknownPacket(Exception):
    pass


def parsePacket(client, data, columns=None):
    orig_data = data

    try:
        tag, data = parseBytes(1, data)

        if tag == 'E':
            error, data = parseString(data)
            return ErrorPacket(error), data

        if tag == 'N':
            error, data = parseString(data)
            return NoticeResponsePacket(error), data

        if tag == 'R':
            auth, data = parseInt32(data)
            return AuthenticationPacket(auth), data

        if tag == 'K':
            pid, data = parseInt32(data)
            key, data = parseInt32(data)
            return BackendKeyDataPacket(pid, key), data

        if tag == 'Z':
            return ReadyForQueryPacket(), data

        if tag == 'P':
            name, data = parseString(data)
            return CursorResponsePacket(name), data

        if tag == 'I':
            unused, data = parseString(data)
            return EmptyQueryResponsePacket(), data

        if tag == 'T':
            count, data = parseInt16(data)
            columns = []
            for i in range(count):
                name, data = parseString(data)
                type_oid, data = parseInt32(data)
                type_size, data = parseInt16(data)
                type_modifier, data = parseInt32(data)
                columns.append((name, (type_oid, type_size, type_modifier)))
            return RowDescriptionPacket(tuple(columns)), data

        if tag == 'D':
            field_count = len(columns)
            if field_count % 8 == 0:
                bytes = field_count / 8
            else:
                bytes = field_count / 8 + 1
            bitmap, data = parseBytes(bytes, data)
            bitmap = array.array('B', bitmap)

            fields = []
            mask = 1 << 8
            for i in range(field_count):
                mask = mask >> 1
                if mask == 0:
                    mask = 1 << 7
                    del bitmap[0]

                if not bitmap[0] & mask:
                    fields.append(None)

                else:
                    size, data = parseInt32(data)
                    value, data = parseBytes(size - 4, data)
                    fields.append(value)

            return AsciiRowPacket(fields), data

        if tag == 'C':
            cmd, data = parseString(data)
            return CompletedResponsePacket(cmd), data

    except IncompletePacket:
        return None, orig_data

    raise UnknownPacket(orig_data)

class PostgresqlClientFactory:
    def __init__(self, user, password='', database='', args='', tty=''):
        self.user = user
        self.password = password
        self.database = database
        self.args = args
        self.tty = tty

    def connected(self, transport):
        cl = PostgresqlClient(transport)
        cl.factory = self
        cl.connected()
        return cl
    
# FIXME -- From the Postgresql Developers Manual section 4.2.1:
#
# A frontend must be prepared to accept ErrorResponse and NoticeResponse
# messages whenever it is expecting any other type of message.
#
# Actually, it is possible for NoticeResponse to arrive even when the frontend
# is not expecting any kind of message, that is, the backend is nominally idle.
# (In particular, the backend can be commanded to terminate by its postmaster.
# In that case it will send a NoticeResponse before closing the connection.) It
# is recommended that the frontend check for such asynchronous notices just
# before issuing any new command.
#
# Also, if the frontend issues any listen(l) commands then it must be prepared
# to accept NotificationResponse messages at any time; see below.

class PostgresqlClient:
    def __init__(self, transport):
        self.transport = transport

        self.buffer = ''

    def connected(self):
        self._sendPacket(StartupPacket(self.factory.user, self.factory.database))
        reply = self._readPacket(AuthenticationPacket)
        if not reply.authentication == 0:
            s = 'Got request for unsupported authentication: %d' % reply.authentication
            raise ProtocolError, s
        reply = self._readPacket(BackendKeyDataPacket)
        reply = self._readPacket(ReadyForQueryPacket)

    def query(self, query):
        self._sendPacket(QueryPacket(query))

        result = None
        err = None
        columns = None
        while 1:
            packet = self._readPacket(columns=columns)
            type = packet.__class__

            if type is CursorResponsePacket:
                pass

            elif type is ReadyForQueryPacket:
                if err:
                    raise err[0], err[1]
                return result

            elif type is NoticeResponsePacket:
                if packet.message.startswith('NOTICE:  COMMIT: no transaction in progress'):
                    err = error.ProgrammingError, 'no transaction in progress'
                elif packet.message.startswith('NOTICE:  ROLLBACK: no transaction in progress'):
                    err = error.ProgrammingError, 'no transaction in progress'

            elif type is CompletedResponsePacket:
                words = packet.command.split()
                if words[0] == 'SELECT':
                    result = dummy.DummyCursor(columns, rows)
                elif len(words) == 1:
                    result = None
                elif words[0] == 'INSERT':
                    oid, rows = map(int, words[1:])
                    if oid == 0:
                        oid = None
                    result = oid, rows
                elif words[0] == 'DELETE':
                    result = int(words[1])
                elif words[0] == 'UPDATE':
                    result = int(words[1])
                else:
                    err = error.InterfaceError, 'got CompletedResponsePacket with unexpected text "%s"' % packet.command

            elif type is RowDescriptionPacket:
                columns = packet.columns
                rows = []
            elif type is AsciiRowPacket:
                rows.append(packet.columns)

            elif type is EmptyQueryResponsePacket:
                self._readPacket(CompletedResponsePacket)
                return
            
            else:
                self.transport.close()
                raise error.InterfaceError, 'got unexpected %s' % `packet`

    def begin(self):
        self.query('BEGIN TRANSACTION')
    def commit(self):
        self.query('COMMIT')
    def rollback(self):
        self.query('ROLLBACK')

    def close(self):
        self._sendPacket(TerminatePacket())
        self.transport.close()

    def _sendPacket(self, p):
        p.send(self.transport)

    def _readPacket(self, expected=None, columns=None):
        while 1:
            packet, self.buffer = parsePacket(self, self.buffer, columns)
    
            if packet:
                if packet.__class__ is ErrorPacket:
                    raise error.ProgrammingError, packet.message
                else:
                    break

            self.buffer = self.buffer + self.transport.read()

        if expected and not packet.__class__ is expected:
            self.transport.close()
            raise error.InterfaceError, 'got unexpected %s when we wanted %s' % (`packet`, `expected`)

        return packet

__all__ = ['PostgresqlClient', 'PostgresqlClientFactory']
