# vim:nowrap:textwidth=0

from socket import htons, htonl, ntohs, ntohl
import struct
import string
import array

from sheared.protocol import basic

class AuthenticationError(Exception):
    pass

class ProtocolError(Exception):
    pass

class BackendError(Exception):
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

class UnknownPacket(Exception):
    pass


def parsePacket(client, data, columns=None):
    orig_data = data

    try:
        tag, data = parseBytes(1, data)

        if tag == 'E':
            error, data = parseString(data)
            return ErrorPacket(error), data

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

class PostgresqlClient(basic.Protocol):
    def __init__(self, reactor, transport, user, password='', database='', args='', tty=''):
        basic.Protocol.__init__(self, reactor, transport)

        self.user = user
        self.password = password
        self.database = database
        self.backend_args = args
        self.backend_tty = tty

        self.buffer = ''

        self.sendPacket(StartupPacket(self.user, self.database))
        reply = self.readPacket(AuthenticationPacket)
        if not reply.authentication == 0:
            s = 'Got request for unsupported authentication: %d' % reply.authentication
            raise AuthenticationError, s
        reply = self.readPacket(BackendKeyDataPacket)
        reply = self.readPacket(ReadyForQueryPacket)
          
    def query(self, query):
        self.sendPacket(QueryPacket(query))

        columns = None
        while 1:
            packet = self.readPacket(columns=columns)
            type = packet.__class__

            if type is CursorResponsePacket:
                pass

            elif type is RowDescriptionPacket:
                columns = packet.columns
                rows = []

            elif type is AsciiRowPacket:
                rows.append(packet.columns)

            elif type is CompletedResponsePacket:
                self.readPacket(ReadyForQueryPacket)
                break

            elif type is EmptyQueryResponsePacket:
                self.readPacket(CompletedResponsePacket)
                return
            
            elif type is ErrorPacket:
                self.readPacket(CompletedResponsePacket)
                raise BackendError, packet.message

            else:
                self.transport.close()
                raise ProtocolError, 'got unexpected %s' % `packet`
                
        return columns, rows

    def terminate(self):
        self.sendPacket(TerminatePacket())
        self.transport.close()

    def sendPacket(self, p, force=0):
        p.send(self.transport)

    def readPacket(self, expected=None, columns=None):
        while 1:
            packet, self.buffer = parsePacket(self, self.buffer, columns)
            if not packet is None:
                break
            self.buffer = self.buffer + self.transport.read()
        if packet.__class__ is ErrorPacket:
            print packet.message
        if expected and not packet.__class__ is expected:
            self.transport.close()
            raise ProtocolError, 'got unexpected %s when we wanted %s' % (`packet`, `expected`)
        return packet

#        while len(self.buffer) > 0:
#            try:
#                packet, self.buffer = parsePacket(self, self.buffer)
#                
#                if packet is None:
#                    break
#
#                type = packet.__class__
#                if type is AuthenticationPacket:
#                    if packet.authentication == 0:
#                        self.observer.connectionMade(self)
#                    else:
#                        s = 'Got request for unsupported ' + \
#                            'authentication: %d' % packet.authentication
#                        self.observer.protocolError(self, s)
#                        self.terminate()
#
#                elif type is BackendKeyDataPacket:
#                    self.backend_key = packet
#
#                elif type is ReadyForQueryPacket:
#                    self.ready = 1
#                    self.observer.readyForQuery(self)
#
#                elif type is RowDescriptionPacket:
#                    self.row_description = packet.columns
#                    self.observer.receivedHead(self, self.row_description)
#                
#                elif type is ErrorPacket:
#                    self.observer.backendError(self, packet.message)
#
#                elif type is CursorResponsePacket:
#                    pass
#
#                elif type is AsciiRowPacket:
#                    self.observer.receivedRow(self, packet.columns)
#
#                elif type is CompletedResponsePacket:
#                    self.observer.queryDone(self)
#
#                elif type is EmptyQueryResponsePacket:
#                    self.observer.queryDone(self)
#
#                else:
#                    s = 'Got a "%s" I do not know what to do with!' % \
#                        packet.__class__.__name__
#                    self.observer.protocolError(self, s)
#
#            except UnknownPacket, e:
#                s = 'Unknown packet: %s' % `e.args[0]`
#                self.observer.protocolError(self, s)
#                self.terminate()
#                self.buffer = ''

__all__ = ['PostgresqlClient', 'PostgresqlClientFactory']
