#include "Python.h"

#include <stdio.h>
#include <unistd.h>
#include <aio.h>
#include <signal.h>

struct _aiocb {
    int op;
    struct aiocb cb;
};

static sigset_t aio_sigset;
static int aio_signal = -1;
static PyObject* aio_setsignal(PyObject *self, PyObject *args)
{
    if(aio_signal != -1) {
        PyErr_SetString(PyExc_RuntimeError, "setsignal already called");
        return NULL;
    }
    if(! PyArg_ParseTuple(args, "i", &aio_signal))
        return NULL;

    sigemptyset(&aio_sigset);
    sigaddset(&aio_sigset, aio_signal);
    if(sigprocmask(SIG_BLOCK, &aio_sigset, NULL)) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* aio_wait(PyObject *self, PyObject *args)
{
    siginfo_t siginf;
    struct _aiocb *cb;
    int rv;
    PyObject *pv;

    if(aio_signal == -1) {
        PyErr_SetString(PyExc_RuntimeError, "setsignal not called");
        return NULL;
    }
    if(! PyArg_ParseTuple(args, ""))
        return NULL;

    sigwaitinfo(&aio_sigset, &siginf);
    cb = siginf.si_ptr;
    rv = aio_return(&cb->cb);

    if(rv >= 0) {
        if(cb->op == 1) {
            pv = Py_BuildValue("iss#", cb->cb.aio_fildes, "read", cb->cb.aio_buf, rv);
        } else if(cb->op == 2) {
            pv = Py_BuildValue("isi", cb->cb.aio_fildes, "write", rv);
        } else {
            PyErr_SetString(PyExc_RuntimeError, "cb->op has an impossible value");
            pv = NULL;
        }
    } else {
        /* FIXME -- need to return which operation and what fd */
        PyErr_SetString(PyExc_IOError, "aio operation failed");
        pv = NULL;
    }

    free((void*)cb->cb.aio_buf);
    free(cb);

    return pv;
}

static PyObject* _aio_read(PyObject *self, PyObject *args)
{
    struct _aiocb *cb;

    if(aio_signal == -1) {
        PyErr_SetString(PyExc_RuntimeError, "setsignal not called");
        return NULL;
    }

    cb = calloc(1, sizeof(struct aiocb));
    if(! PyArg_ParseTuple(args, "iii", &cb->cb.aio_fildes, &cb->cb.aio_nbytes, &cb->cb.aio_offset)) {
        free(cb);
        return NULL;
    }

    cb->op = 1;
    cb->cb.aio_buf = malloc(cb->cb.aio_nbytes);
    cb->cb.aio_sigevent.sigev_value.sival_ptr = cb;
    cb->cb.aio_sigevent.sigev_signo = aio_signal;
    cb->cb.aio_sigevent.sigev_notify = SIGEV_SIGNAL;

    if(aio_read(&cb->cb) < 0) {
        free((void*)cb->cb.aio_buf);
        free(cb);
        return PyErr_SetFromErrno(PyExc_OSError);
    }

    return PyCObject_FromVoidPtr(cb, NULL);
}

static PyObject* _aio_write(PyObject *self, PyObject *args)
{
    struct _aiocb *cb;
    void *buf;

    if(aio_signal == -1) {
        PyErr_SetString(PyExc_RuntimeError, "setsignal not called");
        return NULL;
    }

    cb = calloc(1, sizeof(struct aiocb));
    if(! PyArg_ParseTuple(args, "is#i", &cb->cb.aio_fildes, &buf, &cb->cb.aio_nbytes, &cb->cb.aio_offset)) {
        free(cb);
        return NULL;
    }

    cb->op = 2;
    cb->cb.aio_buf = malloc(cb->cb.aio_nbytes);
    memcpy((void*)cb->cb.aio_buf, buf, cb->cb.aio_nbytes);
    cb->cb.aio_sigevent.sigev_value.sival_ptr = cb;
    cb->cb.aio_sigevent.sigev_signo = aio_signal;
    cb->cb.aio_sigevent.sigev_notify = SIGEV_SIGNAL;

    if(aio_write(&cb->cb) < 0) {
        free((void*)cb->cb.aio_buf);
        free(cb);
        return PyErr_SetFromErrno(PyExc_OSError);
    }

    return PyCObject_FromVoidPtr(cb, NULL);
}

static PyMethodDef AIOMethods[] = {
    {"setsignal", aio_setsignal, METH_VARARGS, "setsignal(signal)\n"},
    {"wait", aio_wait, METH_VARARGS, ""},
    {"read", _aio_read, METH_VARARGS, ""},
    {"write", _aio_write, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

void initaio(void)
{
    (void) Py_InitModule("aio", AIOMethods);
}
