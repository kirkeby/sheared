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
import warnings
import signal
import os

from sheared.python import daemonize
from sheared.python import conffile
from sheared.python import log
from sheared.python.logfile import LogFile
from sheared.python.bitbucket import BitBucket
from sheared.python.proctitle import setproctitle
from sheared import reactor

app_options = [
   [ 'help',         0, 'help',      '',  'help',       '',
     'Display (this) help on command-line arguments.' ],
     
   [ 'help',         0, 'conf-help', '',  'conf-help','',
     'Display help on configuration-file variables.' ],

   [ 'kill',         0, 'stop',      '',  'kill', '',
     'Kill a daemonized, running instance of this\n'
     'application.' ],
     
   [ 'kill',         0, 'restart',   '',  'restart', '',
     'Restart a daemonized, running instance of this\n'
     'application.' ],
     
   [ 'set_bool',     0, 'daemonize', '',  'daemonize',  'application.daemonize',
     'Run as a UNIX daemon process (implies log-file\n'
     'and pid-file).' ],
     
   [ 'clear_bool',   0, 'daemonize', '',  'foreground', 'application.foreground',
     'Run in the foreground.' ],
     
   [ 'set_str',      1, 'logfile',   'l', 'log-file',   'application.log-file',
     'Write messages to file.' ],
     
   [ 'set_str',      1, 'pidfile',   'p', 'pid-file',   'application.pid-file',
     'Write pid-file.' ],

   [ 'set_int',      1, 'user',      'u', 'user',       'application.user',
     'Change to this uid after configuring application.' ],
     
   [ 'set_int',      1, 'group',     'g', 'group',      'application.group',
     'Change to this gid after configuring application.' ],
     
   [ 'opt_conf',     1, '',          'c', 'conf-file',  '',
     'Read configuration file (may be given multiple\n'
     'times).' ],

   [ 'opt_confstmt', 1, '',          'C', 'conf',       '',
     'Set one configuration-file variable from\n'
     'command-line.' ],
]

class Application:
    def __init__(self, name, options):
        self.name = name
        self.description = ''

        self.conf_files = ['/etc/%s.conf', '~/.%s.conf']
        self.conf_files = [c % self.name for c in self.conf_files]

        self.options = []
        self.options.extend(app_options)
        self.options.extend(options)

        self.daemonize = 0
        self.logfile = self.name + '.log'
        self.pidfile = self.name + '.pid'

        self.user = None
        self.group = None

        self.reactor = reactor

        self.do_restart = 0

    def kill(self, name, _):
        if not self.pidfile:
            print "Error: No pid-file path given."
            sys.exit(1)
    
        if name == 'stop':
            sig = signal.SIGINT
        elif name == 'restart':
            sig = signal.SIGHUP
        else:
            raise 'Pigs can fly!'

        try:
            pid = int(open(self.pidfile, 'r').readline().strip())
        except:
            _, e, _ = sys.exc_info()
            print '%s: %s' % (self.pidfile, e.strerror)
            sys.exit(1)

        os.kill(pid, sig)
        sys.exit(0)

    def help(self, name, _):
        if self.description:
            print "   ", self.description
            print "   ", "=" * len(self.description)
            print
        if name == 'help':
            self.help_argv()
        elif name == 'conf-help':
            self.help_conf()
        sys.exit(0)

    def help_argv(self):
        print "Usage: %s" % self.usage()

        for handler, value, name, short, long, conf, description in self.options:
            if short or long:
                break
        else:
            return

        print
        print "Options:"
        for handler, value, name, short, long, conf, description in self.options:
            if not (short or long):
                continue
            if not description:
                description = '[No description available.]'

            if short:
                s = '-%s ' % short
            else:
                s = '   '

            if long:
                s = s + '--%s ' % long
                if len(long) <= 20:
                    s = s + ' ' * (20 - len(long))
                else:
                    s = s + '\n' + ' ' * 26
            else:
                s = s + ' ' * 23

            s = s + description.replace('\n', '\n' + ' ' * 28)
            print '  ' + s

    def usage(self):
        return "%s [options]" % self.name

    def help_conf(self):
        for handler, value, name, short, long, conf, description in self.options:
            if conf:
                break
        else:
            print "Nothing to configure."
            return

        print "Available configuration-file variables:"
        for handler, value, name, short, long, conf, description in self.options:
            if not conf:
                continue
            if not description:
                description = '[No description available.]'

            print
            print conf
            print '  ' + description.replace('\n', '\n  ')

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
        for handler, value, name, short, long, conf, description in self.options:
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
        for handler, value, name, short, long, conf, description in self.options:
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
            for handler, value, name, short, long, conf, description in self.options:
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

        def _stop(s, f):
            if s == signal.SIGTERM:
                os._exit(3)
            if s == signal.SIGHUP:
                self.do_restart = 1
            self.stop()
        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGHUP, _stop)

        daemonize.closeall(min=3)

        os.umask(0)

        self.setup()
        self.start()
        try:
            self.teardown()
        except:
            log.default.exception(sys.exc_info())

        if self.do_restart:
            self.restart()

    def setup(self):
        pass

    def teardown(self):
        pass

    def start(self):
        setproctitle(self.name)

        if self.daemonize and self.logfile:
            log.default = LogFile(self.logfile)
            warnings.showwarning = log.showwarning

        try:
            if self.daemonize:
                daemonize.background(chdir=0, close=0)
                daemonize.openstdio()

                if self.pidfile:
                    daemonize.writepidfile(self.pidfile)

            if not self.group is None:
                os.setgid(self.group)
            if not self.user is None:
                os.setuid(self.user)

            if hasattr(self, 'run'):
                name = '<Main for %r>' % self
                self.reactor.createtasklet(self.run, name=name)
    
            log.default.normal('%s starting' % self.name)
            log.default.close()

            self.reactor.start()

            log.default.close()
            if self.do_restart:
                log.default.normal('%s restarting' % self.name)
            else:
                log.default.normal('%s done' % self.name)

        except:
            log.default.close()
            log.default.exception(sys.exc_info())
            os._exit(1)

    def restart(self):
        daemonize.closeall(min=3)

        argv = [sys.executable]
        argv.extend(sys.argv)

        try:
            os.execv(argv[0], argv)
        except:
            pass
        os._exit(2)

    def stop(self):
        self.reactor.stop()