# vim:nowrap:textwidth=0
#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby <sune@mel.interspace.dk>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from socket import htons, htonl, ntohs, ntohl
import struct
import string
import array
import crypt
import encodings

from sheared.database import error
from sheared.database import dummy

str_encoder, str_decoder = encodings.search_function('utf8')[:2]

# Postgresql -> Python type mappings, type-OIDs lifted from
# /usr/include/postgresql/server/catalog/pg_type.h
pg_type = {
        16:   lambda s: s == 't',           # bool
        20:   long,                         # int8
        21:   int,                          # int2
        23:   int,                          # int4
        25:   lambda s: str_decoder(s)[0],  # text
        1042: lambda s: str_decoder(s)[0],  # char(length)
        1043: lambda s: str_decoder(s)[0],  # varchar(length)
    }

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

class PasswordPacket:
    def __init__(self, password):
        self.password = password

    def send(self, transport):
        s = formatString(self.password)
        transport.write(formatInt32(len(s) + 4) + s)

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
            p = AuthenticationPacket(auth)
            if auth == 0:
                p.authentication = 'OK'
            elif auth == 1:
                p.authentication = 'KerberosV4'
            elif auth == 2:
                p.authentication = 'KerberosV5'
            elif auth == 3:
                p.authentication = 'CleartextPassword'
            elif auth == 4:
                p.authentication = 'CryptPassword'
                p.salt, data = parseBytes(2, data)
            elif auth == 5:
                p.authentication = 'MD5Password'
                p.salt, data = parseBytes(4, data)
            elif auth == 6:
                p.authentication = 'SCMCredential'
            else:
                raise ProtocolError, 'Unknown Authentication type: %d' % auth
            return p, data

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
                desc = dummy.DummyRowDescription(name, type_oid, type_size)
                columns.append(desc)
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

    def authenticate(self, user, password='', database='', args='', tty=''):
        self._sendPacket(StartupPacket(user, database))
        reply = self._readPacket(AuthenticationPacket)

        if reply.authentication == 'OK':
            pass
        
        elif reply.authentication == 'CryptPassword':
            crypted = crypt.crypt(password, reply.salt)
            self._sendPacket(PasswordPacket(crypted))
            reply = self._readPacket(AuthenticationPacket)
    
        else:
            s = 'Got request for unsupported authentication: %d' % reply.authentication
            raise ProtocolError, s

        if reply.authentication == 'OK':
            reply = self._readPacket(BackendKeyDataPacket)
            reply = self._readPacket(ReadyForQueryPacket)

    def _quote(self, str, q):
        return q + str.replace('\\', '\\\\').replace(q, '\\' + q) + q
    def quote_str(self, str):
        if str is None:
            return 'NULL'
        else:
            return self._quote(str_encoder(str)[0], "'")
    def quote_name(self, str):
        if str is None:
            return 'NULL'
        else:
            return self._quote(str, '"')
    def quote_bool(self, b):
        if b is None:
            return 'NULL'
        elif b:
            return 'true'
        else:
            return 'false'

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

            elif type is ErrorPacket:
                err = error.ProgrammingError, packet.message

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
                    try:
                        for r in range(len(rows)):
                            for c in range(len(columns)):
                                if not rows[r][c] is None:
                                    # FIXME -- s/, None//?
                                    conv = pg_type.get(columns[c].type, None)
                                    rows[r][c] = conv(rows[r][c])
                    except KeyError:
                        raise ProtocolError, 'no converter for pg_type OID %d' % columns[c].type
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
                elif words[0] == 'CREATE':
                    result = None
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
                del self.transport
                raise error.InterfaceError, 'got unexpected %s' % `packet`

        raise 'internal error; branch should never execute'

    def begin(self):
        self.query('BEGIN TRANSACTION')
    def commit(self):
        self.query('COMMIT')
    def rollback(self):
        self.query('ROLLBACK')

    def close(self):
        if hasattr(self, 'transport'):
            self._sendPacket(TerminatePacket())
            self.transport.close()
            del self.transport

    def _sendPacket(self, p):
        p.send(self.transport)

    def _readPacket(self, expected=None, columns=None):
        while 1:
            packet, self.buffer = parsePacket(self, self.buffer, columns)
    
            if packet:
                break

            self.buffer = self.buffer + self.transport.read(4096)

        if expected and not packet.__class__ is expected:
            if packet.__class__ is ErrorPacket:
                raise error.ProgrammingError, packet.message
            self.transport.close()
            del self.transport
            raise error.InterfaceError, 'got unexpected %s when we wanted %s' % (`packet`, `expected`)

        return packet

__all__ = ['PostgresqlClient', 'PostgresqlClientFactory']
