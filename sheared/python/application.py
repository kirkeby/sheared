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
   [ 'set_bool',   0, 'daemonize', '',  'daemonize',  'application.daemonize' ],
   [ 'clear_bool', 0, 'daemonize', '',  'foreground', 'application.foreground' ],
   [ 'set_str',    1, 'logfile',   'l', 'log-file',   'application.log-file' ],
   [ 'set_str',    1, 'pidfile',   'p', 'pid-file',   'application.pid-file' ],
   [ 'parse_conf_opt', 1, '',      'c', 'conf-file',  '' ],
]

class Application:
    def __init__(self, name, options):
        self.name = name

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
    
    def parse_conf_opt(self, _, path):
        self.parse_conf(path)


    def parse_conf(self, path):
        self.parse_conffd(open(path, 'r'))

    def parse_conffd(self, file):
        for opt, val in conffile.parsefd(file):
            for handler, value, name, short, long, conf in self.options:
                if opt == conf:
                    break
            else:
                raise 'Unknown option: %s' % opt
            
            try:
                getattr(self, handler)(name, val)
            except:
                raise 'Internal error: handler failed: %r' % handler
       
    
    def parse_argv(self, argv):
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

            try:
                getattr(self, handler)(name, val)
            except:
                raise 'Internal error: handler failed: %r' % handler

        return args

    def main(self, conf=None, argv=sys.argv):
        if conf:
            self.parse_conf(conf)
    
        conf = os.path.expanduser('~/.%src' % self.name)
        if os.access(conf, os.R_OK):
            self.parse_conf(conf)

        self.parse_argv(argv)

        self.start()

    def start(self):
        if self.daemonize and not self.logfile:
            self.logfile = self.name + '.log'
        if self.daemonize and not self.pidfile:
            self.pidfile = self.name + '.pid'

        def stop(signum, frame):
            self.stop()
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

        daemonize.closeall(min=3)

        if self.logfile:
            dameonize.openstdlog(self.logfile)

        if self.daemonize:
            daemonize.background(chdir=0, close=0)
            if not self.logfile:
                daemonize.openstdio()

        if self.pidfile:
            daemonize.writepidfile(self.pidfile)

        self.reactor.createtasklet(self.run)
        self.reactor.start()

    def stop(self):
        self.reactor.stop()

    def run(self):
        raise NotImplementedError
