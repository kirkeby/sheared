#include "Python.h"

static PyObject* cabml_lex_outer(PyObject *self, PyObject *args)
{
    PyObject *l;
    char *i, *j, *end;
    char quotes = 0;
    int  escaped = 0;
    int  len;

    if(! PyArg_ParseTuple(args, "s#", &i, &len))
        return NULL;
    end = i + len;

    l = PyList_New(0);
    if(l == NULL)
        return NULL;

    while(i < end) {
        /* find beginning of next tag, */
        for(j = i; j < end; ++j)
            if(*j == '<')
                break;

        if(j == end) {
            /* no more tags, done */
            if(PyList_Append(l, Py_BuildValue("ss", "text", i))) {
                Py_DECREF(l);
                return NULL;
            }
            break;
        } else if(j > i) {
            /* there is text between here and next tag */
            if(PyList_Append(l, Py_BuildValue("ss#", "text", i, j-i))) {
                Py_DECREF(l);
                return NULL;
            }
        }
        i = j + 1;

        /* search for end of tag */
        for(; j < end; ++j) {
            if(escaped) {
                escaped = 0;
                continue;
            }
            if(*j == '\\') {
                escaped = 1;
                continue;
            }
            if(quotes) {
                if(*j == quotes)
                    quotes = 0;
                continue;
            }
            if(*j == '>')
                break;
            if(*j == '"' || *j == '\'')
                quotes = *j;
        }
        if(j == end) {
            Py_DECREF(l);
            PyErr_SetString(PyExc_ValueError, "never-ending tag spotted");
            return NULL;
        }

        if(PyList_Append(l, Py_BuildValue("ss#", "tag", i, j-i))) {
            Py_DECREF(l);
            return NULL;
        }
        i = j + 1;
    }

    return (PyObject*)l;
}

static PyMethodDef cabmlmethods[] = {
    {"lex_outer", cabml_lex_outer, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

void initcabml(void)
{
    (void) Py_InitModule("cabml", cabmlmethods);
}
