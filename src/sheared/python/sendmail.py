from sheared.python import commands

def sendmail(to, text):
    argv = ['/usr/lib/sendmail', to]
    pid, stdin, stdout = commands.spawn(argv[0], argv)
    stdin.write(text)
    stdin.close()

    # FIXME -- error handling badly needed!
    #while not stdout.read() == '':
    #    pass
    stdout.close()

    commands.waitpid(pid)
