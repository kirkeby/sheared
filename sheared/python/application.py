# vim:tw=0:nowrap
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
import getopt
import sys
import traceback
import signal
import os

from sheared.python import daemonize
from sheared.python import conffile
from sheared import reactor

app_options = [
   [ 'set_bool',     0, 'daemonize', '',  'daemonize',  'application.daemonize' ],
   [ 'clear_bool',   0, 'daemonize', '',  'foreground', 'application.foreground' ],
   [ 'set_str',      1, 'logfile',   'l', 'log-file',   'application.log-file' ],
   [ 'set_str',      1, 'pidfile',   'p', 'pid-file',   'application.pid-file' ],
   [ 'opt_conf',     1, '',          'c', 'conf-file',  '' ],
   [ 'opt_confstmt', 1, '',          'C', 'conf',       '' ],
]

class Application:
    def __init__(self, name, options):
        self.name = name

        self.conf_files = ['/etc/%s.conf', '~/.%s.conf']
        self.conf_files = [c % self.name for c in self.conf_files]

        self.options = []
        self.options.extend(app_options)
        self.options.extend(options)

        self.daemonize = 0
        self.logfile = None
        self.pidfile = None

        self.reactor = reactor
        
    def set_bool(self, name, value):
        assert not value
        setattr(self, name, 1)
    
    def clear_bool(self, name, value):
        assert not value
        setattr(self, name, 0)
    
    def set_str(self, name, value):
        setattr(self, name, value)

    def set_int(self, name, value):
        setattr(self, name, int(value))
    
    def opt_conf(self, _, path):
        self.parse_conf(path)

    def opt_confstmt(self, _, stmt):
        opt, val = conffile.parsestmt(stmt)
        self.handle_confstmt(opt, val)


    def parse_conf(self, path):
        self.parse_conffd(open(path, 'r'))

    def parse_conffd(self, file):
        for opt, val in conffile.parsefd(file):
            self.handle_confstmt(opt, val)


    def handle_confstmt(self, opt, val):
        for handler, value, name, short, long, conf in self.options:
            if not conf:
                continue
            if opt == conf:
                break
        else:
            raise 'Unknown option: %s' % opt
        
        getattr(self, handler)(name, val)
       
    
    def parse_args(self, argv):
        sopt = ''
        lopt = []
        for handler, value, name, short, long, conf in self.options:
            if short:
                sopt = sopt + short
                if value:
                    sopt = sopt + ':'
            if long:
                if value:
                    lopt.append(long + '=')
                else:
                    lopt.append(long)
        
        opts, args = getopt.getopt(argv, sopt, lopt)

        for opt, val in opts:
            for handler, value, name, short, long, conf in self.options:
                if (opt == '-' + short) or (opt == '--' + long):
                    break
            else:
                raise 'Internal error, dropped an option on the floor: %r' % opt

            getattr(self, handler)(name, val)

        return args

    def main(self, argv=sys.argv):
        for path in self.conf_files:
            conf = os.path.expanduser(path)
            if os.access(conf, os.R_OK):
                self.parse_conf(conf)

        self.parse_args(argv[1:])

        def stop(signum, frame):
            if signum == signal.SIGQUIT:
                sys.exit(0)
            else:
                self.stop()
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGQUIT, stop)

        daemonize.closeall(min=3)

        self.setup()
        self.start()

    def setup(self):
        pass

    def start(self):
        if self.daemonize and not self.logfile:
            self.logfile = self.name + '.log'
        if self.daemonize and not self.pidfile:
            self.pidfile = self.name + '.pid'

        if self.logfile:
            daemonize.openstdlog(self.logfile)

        if self.daemonize:
            daemonize.background(chdir=0, close=0)
            if not self.logfile:
                daemonize.openstdio()

        if self.pidfile:
            daemonize.writepidfile(self.pidfile)

        name = '<Main for %r>' % self
        self.reactor.createtasklet(self.run, name=name)
        self.reactor.start()

    def stop(self):
        self.reactor.stop()

    def run(self):
        raise NotImplementedError
