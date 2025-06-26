#include <Python.h>

static PyObject* fast_hash(PyObject* self, PyObject* args) {
    const char* data;
    Py_ssize_t len;
    if (!PyArg_ParseTuple(args, "y#", &data, &len)) {
        return NULL;
    }
    unsigned long hash = 5381;
    for (Py_ssize_t i = 0; i < len; i++) {
        hash = ((hash << 5) + hash) + (unsigned char)data[i];
    }
    return PyLong_FromUnsignedLong(hash);
}

static PyMethodDef FastMethods[] = {
    {"fast_hash", fast_hash, METH_VARARGS, "Compute a fast hash of bytes"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef fastmodule = {
    PyModuleDef_HEAD_INIT,
    "fast_utils",   /* name of module */
    NULL,           /* module documentation, may be NULL */
    -1,             /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    FastMethods
};

PyMODINIT_FUNC PyInit_fast_utils(void) {
    return PyModule_Create(&fastmodule);
}
