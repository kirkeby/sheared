#include "Python.h"

#include <sys/socket.h>
#include <sys/uio.h>

static struct cmsghdr *cmsg = NULL;
static struct msghdr *msg = NULL;
static struct iovec *iov = NULL;
static int *buf = NULL;
static int *filedesc = NULL;
static int initmsg(void)
{
    if(! cmsg) {
        cmsg = malloc(sizeof(struct cmsghdr) + sizeof(int));
        filedesc = (int *) CMSG_DATA(cmsg);
        msg = malloc(sizeof(struct msghdr));
        iov = malloc(sizeof(struct iovec));
        buf = malloc(UIO_MAXIOV);
    }
    if(! (cmsg && msg && iov && buf)) {
        PyErr_NoMemory();
        return -1;
    }

    memset(cmsg, 0, sizeof(struct cmsghdr) + sizeof(int));
    memset(msg, 0, sizeof(struct msghdr));
    memset(iov, 0, sizeof(struct iovec));

    cmsg->cmsg_level = SOL_SOCKET;
    cmsg->cmsg_type = SCM_RIGHTS;
    cmsg->cmsg_len = sizeof(struct cmsghdr) + sizeof(int);

    msg->msg_iov = iov;
    msg->msg_iovlen = 1;
    msg->msg_name = NULL;
    msg->msg_namelen = 0;
    msg->msg_control = (caddr_t) cmsg;
    msg->msg_controllen = cmsg->cmsg_len;

    iov->iov_base = buf;
    iov->iov_len = UIO_MAXIOV;

    return 0;
}

static PyObject* fdpass_send(PyObject *self, PyObject *args)
{
    int sock, fd, strlen, err;
    char *str;

    if(! PyArg_ParseTuple(args, "iis#", &sock, &fd, &str, &strlen))
        return NULL;

    if(initmsg())
        return NULL;
    
    if(strlen > iov->iov_len) {
        PyErr_SetString(PyExc_RuntimeError, "iovec too long");
        return NULL;
    }
    memcpy(iov->iov_base, str, strlen);
    iov->iov_len = strlen;

    *filedesc = fd;

    err = sendmsg(sock, msg, 0);
    if(err < 0) {
        return PyErr_SetFromErrno(PyExc_IOError);
    }
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* fdpass_recv(PyObject *self, PyObject *args)
{
    int sock, err;

    if(! PyArg_ParseTuple(args, "i", &sock))
        return NULL;

    if(initmsg())
        return NULL;

    err = recvmsg(sock, msg, 0);
    if(err < 0) {
        return PyErr_SetFromErrno(PyExc_IOError);
    }
    if(msg->msg_controllen != sizeof(struct cmsghdr) + sizeof(int)) {
        PyErr_SetString(PyExc_RuntimeError, "no fd received");
        return NULL;
    }
    return Py_BuildValue("is#", *filedesc, iov->iov_base, iov->iov_len);
}

static PyMethodDef FdPassMethods[] = {
    {"send",  fdpass_send, METH_VARARGS, "send(sock, fd, iovec)\nsend fd over socket."},
    {"recv",  fdpass_recv, METH_VARARGS, "recv(sock) -> fd, iovec\nreceive fd over socket."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

void initfdpass(void)
{
    (void) Py_InitModule("fdpass", FdPassMethods);
}
