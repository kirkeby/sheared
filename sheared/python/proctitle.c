/* proctitle code - we know this to work only on linux... */

/*
**  SETPROCTITLE -- set process title for ps (from sendmail)
**
**      Parameters:
**              fmt -- a printf style format string.
**
**      Returns:
**              none.
**
**      Side Effects:
**              Clobbers argv of our main procedure so ps(1) will
**              display the title.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#ifndef SPT_BUFSIZE
#define SPT_BUFSIZE     2048
#endif

extern char** environ;

static char** argv;
static int argv_lth;

/* Python module code */
#include "Python.h"
extern void Py_GetArgcArgv(int *argc, char ***argv);

static PyObject* pt_setproctitle(PyObject* self, PyObject* args)
{
    int i;
    const char *buf;
    
    if(! PyArg_ParseTuple(args, "s", &buf))
        return NULL;

    i = strlen (buf);
    if (i > argv_lth - 2) {
            i = argv_lth - 2;
            buf[i] = '\0';
    }
    memset(argv[0], '\0', argv_lth);       /* clear the memory area */
    (void) strcpy (argv[0], buf);

    argv[1] = NULL;

    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef PTMethods[] = {
    {"setproctitle", pt_setproctitle, METH_VARARGS, "setproctitle(s)\n"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

void initproctitle(void)
{
    int argc;
    
    Py_GetArgcArgv(&argc, &argv);
    argv_lth = argv[argc-1] + strlen(argv[argc-1]) - argv[0];

    (void) Py_InitModule("proctitle", PTMethods);
}
