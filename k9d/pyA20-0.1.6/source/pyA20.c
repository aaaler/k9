/*
 * pyA20.c
 *
 * Copyright 2013 Stanimir Petev <support@olimex.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 */


#include "Python.h"
#include "gpio_lib.h"


static PyObject *SetupException;
static PyObject *OutputException;
static PyObject *InputException;
static PyObject *inp;
static PyObject *out;
static PyObject *per;
static PyObject *high;
static PyObject *low;

//GPIO 1
#define PIN_PG0		SUNXI_GPG(0)
#define PIN_PG1		SUNXI_GPG(1)
#define PIN_PG2		SUNXI_GPG(2)
#define PIN_PG3		SUNXI_GPG(3)
#define PIN_PG4		SUNXI_GPG(4)
#define PIN_PG5		SUNXI_GPG(5)
#define PIN_PG6		SUNXI_GPG(6)
#define PIN_PG7		SUNXI_GPG(7)
#define PIN_PG8		SUNXI_GPG(8)
#define PIN_PG9		SUNXI_GPG(9)
#define PIN_PG10	SUNXI_GPG(10)
#define PIN_PG11	SUNXI_GPG(11)
//#define PIN_PD26	SUNXI_GPD(26)
//#define PIN_PD27	SUNXI_GPD(27)

//GPIO 2
//#define PIN_PB0		SUNXI_GPB(0)
#define PIN_PE0		SUNXI_GPE(0)
//#define PIN_PB1		SUNXI_GPB(1)
#define PIN_PE1		SUNXI_GPE(1)
#define PIN_PI0		SUNXI_GPI(0)
#define PIN_PE2		SUNXI_GPE(2)
#define PIN_PI1		SUNXI_GPI(1)
#define PIN_PE3		SUNXI_GPE(3)
#define PIN_PI2		SUNXI_GPI(2)
#define PIN_PE4		SUNXI_GPE(4)
#define PIN_PI3		SUNXI_GPI(3)
#define PIN_PE5		SUNXI_GPE(5)
#define PIN_PI10	SUNXI_GPI(10)
#define PIN_PE6		SUNXI_GPE(6)
#define PIN_PI11	SUNXI_GPI(11)
#define PIN_PE7		SUNXI_GPE(7)
#define PIN_PC3		SUNXI_GPC(3)
#define PIN_PE8		SUNXI_GPE(8)
#define PIN_PC7		SUNXI_GPC(7)
#define PIN_PE9		SUNXI_GPE(9)
#define PIN_PC16	SUNXI_GPC(16)
#define PIN_PE10	SUNXI_GPE(10)
#define PIN_PC17	SUNXI_GPC(17)
#define PIN_PE11	SUNXI_GPE(11)
#define PIN_PC18	SUNXI_GPC(18)
#define PIN_PI14	SUNXI_GPI(14)
#define PIN_PC23	SUNXI_GPC(23)
#define PIN_PI15	SUNXI_GPI(15)
#define PIN_PC24	SUNXI_GPC(24)
#define PIN_PB23	SUNXI_GPB(23)
#define PIN_PB22	SUNXI_GPB(22)

//GPIO 3
#define PIN_PH0		SUNXI_GPH(0)
#define PIN_PB3		SUNXI_GPB(3)
#define PIN_PH2		SUNXI_GPH(2)
#define PIN_PB4		SUNXI_GPB(4)
#define PIN_PH7		SUNXI_GPH(7)
#define PIN_PB5		SUNXI_GPB(5)
#define PIN_PH9		SUNXI_GPH(9)
#define PIN_PB6		SUNXI_GPB(6)
#define PIN_PH10	SUNXI_GPH(10)
#define PIN_PB7		SUNXI_GPB(7)
#define PIN_PH11	SUNXI_GPH(11)
#define PIN_PB8		SUNXI_GPB(8)
#define PIN_PH12	SUNXI_GPH(12)
#define PIN_PB10	SUNXI_GPB(10)
#define PIN_PH13	SUNXI_GPH(13)
#define PIN_PB11	SUNXI_GPB(11)
#define PIN_PH14	SUNXI_GPH(14)
#define PIN_PB12	SUNXI_GPB(12)
#define PIN_PH15	SUNXI_GPH(15)
#define PIN_PB13	SUNXI_GPB(13)
#define PIN_PH16	SUNXI_GPH(16)
#define PIN_PB14	SUNXI_GPB(14)
#define PIN_PH17	SUNXI_GPH(17)
#define PIN_PB15	SUNXI_GPB(15)
#define PIN_PH18	SUNXI_GPH(18)
#define PIN_PB16	SUNXI_GPB(16)
#define PIN_PH19	SUNXI_GPH(19)
#define PIN_PB17	SUNXI_GPB(17)
#define PIN_PH20	SUNXI_GPH(20)
#define PIN_PH24	SUNXI_GPH(24)
#define PIN_PH21	SUNXI_GPH(21)
#define PIN_PH25	SUNXI_GPH(25)
#define PIN_PH22	SUNXI_GPH(22)
#define PIN_PH26	SUNXI_GPH(26)
#define PIN_PH23	SUNXI_GPH(23)
#define PIN_PH27	SUNXI_GPH(27)


static int module_setup(void) {
    int result;

    result = sunxi_gpio_init();
    if(result == SETUP_DEVMEM_FAIL) {
        PyErr_SetString(SetupException, "No access to /dev/mem. Try running as root!");
        return SETUP_DEVMEM_FAIL;
    }
    else if(result == SETUP_MALLOC_FAIL) {
        PyErr_NoMemory();
        return SETUP_MALLOC_FAIL;
    }
    else if(result == SETUP_MMAP_FAIL) {
        PyErr_SetString(SetupException, "Mmap failed on module import");
        return SETUP_MMAP_FAIL;
    }
    else {
        return SETUP_OK;
    }

    return SETUP_OK;
}






static PyObject* py_output(PyObject* self, PyObject* args) {
    int gpio;
    int value;

    if(!PyArg_ParseTuple(args, "ii", &gpio, &value))
        return NULL;

    if(value != 0 && value != 1) {
        PyErr_SetString(OutputException, "Invalid output state");
        return NULL;
    }

    if(sunxi_gpio_get_cfgpin(gpio) != SUNXI_GPIO_OUTPUT) {
        PyErr_SetString(OutputException, "GPIO is no an output");
        return NULL;
    }
    sunxi_gpio_output(gpio, value);

    Py_RETURN_NONE;
}
static PyObject* py_input(PyObject* self, PyObject* args) {
    int gpio;
    int result;

    if(!PyArg_ParseTuple(args, "i", &gpio))
        return NULL;

    if(sunxi_gpio_get_cfgpin(gpio) != SUNXI_GPIO_INPUT) {
        PyErr_SetString(InputException, "GPIO is not an input");
        return NULL;
    }
    result = sunxi_gpio_input(gpio);

    if(result == -1) {
        PyErr_SetString(InputException, "Reading pin failed");
        return NULL;
    }


    return Py_BuildValue("i", result);
}

static PyObject* py_setcfg(PyObject* self, PyObject* args) {
    int gpio;
    int direction;

    if(!PyArg_ParseTuple(args, "ii", &gpio, &direction))
        return NULL;

    if(direction != 0 && direction != 1 && direction != 2) {
        PyErr_SetString(SetupException, "Invalid direction");
        return NULL;
    }
    sunxi_gpio_set_cfgpin(gpio, direction);

    Py_RETURN_NONE;
}
static PyObject* py_getcfg(PyObject* self, PyObject* args) {
    int gpio;
    int result;


    if(!PyArg_ParseTuple(args, "i", &gpio))
        return NULL;

    result = sunxi_gpio_get_cfgpin(gpio);


    return Py_BuildValue("i", result);


}
static PyObject* py_init(PyObject* self, PyObject* args) {

    module_setup();

    Py_RETURN_NONE;
}
static PyObject* py_cleanup(PyObject* self, PyObject* args) {

    sunxi_gpio_cleanup();
    Py_RETURN_NONE;
}


PyMethodDef module_methods[] = {
    {"init", py_init, METH_NOARGS, "Initialize module"},
    {"cleanup", py_cleanup, METH_NOARGS, "munmap /dev/map."},
    {"setcfg", py_setcfg, METH_VARARGS, "Set direction."},
    {"getcfg", py_getcfg, METH_VARARGS, "Get direction."},
    {"output", py_output, METH_VARARGS, "Set output state"},
    {"input", py_input, METH_VARARGS, "Get input state"},
    {NULL, NULL, 0, NULL}
};
#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "A20 module",
    NULL,
    -1,
    module_methods
};
#endif
PyMODINIT_FUNC initA20_GPIO(void) {
    PyObject* module = NULL;


#if PY_MAJOR_VERSION >= 3
    module = PyModule_Create(&module_methods);
#else
    module = Py_InitModule("A20_GPIO", module_methods);
#endif


    if(module == NULL)
#if PY_MAJOR_VERSION >= 3
        return module;
#else
        return;
#endif



    SetupException = PyErr_NewException("PyA20.SetupException", NULL, NULL);
    PyModule_AddObject(module, "SetupException", SetupException);
    OutputException = PyErr_NewException("PyA20.OutputException", NULL, NULL);
    PyModule_AddObject(module, "OutputException", OutputException);
    InputException = PyErr_NewException("PyA20.InputException", NULL, NULL);
    PyModule_AddObject(module, "InputException", InputException);



    high = Py_BuildValue("i", HIGH);
    PyModule_AddObject(module, "HIGH", high);

    low = Py_BuildValue("i", LOW);
    PyModule_AddObject(module, "LOW", low);

    inp = Py_BuildValue("i", INPUT);
    PyModule_AddObject(module, "INPUT", inp);

    out = Py_BuildValue("i", OUTPUT);
    PyModule_AddObject(module, "OUTPUT", out);

    per = Py_BuildValue("i", PER);
    PyModule_AddObject(module, "PER", per);


// GPIO-1
    PyModule_AddObject(module, "PIN1_5", Py_BuildValue("i", PIN_PG0));
	PyModule_AddObject(module, "PIN1_7", Py_BuildValue("i", PIN_PG1));
	PyModule_AddObject(module, "PIN1_9", Py_BuildValue("i", PIN_PG2));
	PyModule_AddObject(module, "PIN1_11", Py_BuildValue("i", PIN_PG3));
	PyModule_AddObject(module, "PIN1_13", Py_BuildValue("i", PIN_PG4));
	PyModule_AddObject(module, "PIN1_15", Py_BuildValue("i", PIN_PG5));
	PyModule_AddObject(module, "PIN1_17", Py_BuildValue("i", PIN_PG6));
	PyModule_AddObject(module, "PIN1_19", Py_BuildValue("i", PIN_PG7));
	PyModule_AddObject(module, "PIN1_21", Py_BuildValue("i", PIN_PG8));
	PyModule_AddObject(module, "PIN1_23", Py_BuildValue("i", PIN_PG9));
	PyModule_AddObject(module, "PIN1_25", Py_BuildValue("i", PIN_PG10));
	PyModule_AddObject(module, "PIN1_27", Py_BuildValue("i", PIN_PG11));
	//PyModule_AddObject(module, "PIN1.29", Py_BuildValue("i", PIN_PD26));
	//PyModule_AddObject(module, "PIN1.31", Py_BuildValue("i", PIN_PD27));

// GPIO-2
    //PyModule_AddObject(module, "PIN2.5", Py_BuildValue("i", PIN_PB0));
    PyModule_AddObject(module, "PIN2_6", Py_BuildValue("i", PIN_PE0));
    //PyModule_AddObject(module, "PIN2.7", Py_BuildValue("i", PIN_PB1));
    PyModule_AddObject(module, "PIN2_8", Py_BuildValue("i", PIN_PE1));
    PyModule_AddObject(module, "PIN2_9", Py_BuildValue("i", PIN_PI0));
    PyModule_AddObject(module, "PIN2_10", Py_BuildValue("i", PIN_PE2));
    PyModule_AddObject(module, "PIN2_11", Py_BuildValue("i", PIN_PI1));
    PyModule_AddObject(module, "PIN2_12", Py_BuildValue("i", PIN_PE3));
    PyModule_AddObject(module, "PIN2_13", Py_BuildValue("i", PIN_PI2));
    PyModule_AddObject(module, "PIN2_14", Py_BuildValue("i", PIN_PE4));
    PyModule_AddObject(module, "PIN2_15", Py_BuildValue("i", PIN_PI3));
    PyModule_AddObject(module, "PIN2_16", Py_BuildValue("i", PIN_PE5));
    PyModule_AddObject(module, "PIN2_17", Py_BuildValue("i", PIN_PI10));
    PyModule_AddObject(module, "PIN2_18", Py_BuildValue("i", PIN_PE6));
    PyModule_AddObject(module, "PIN2_19", Py_BuildValue("i", PIN_PI11));
    PyModule_AddObject(module, "PIN2_20", Py_BuildValue("i", PIN_PE7));
    PyModule_AddObject(module, "PIN2_21", Py_BuildValue("i", PIN_PC3));
    PyModule_AddObject(module, "PIN2_22", Py_BuildValue("i", PIN_PE8));
    PyModule_AddObject(module, "PIN2_23", Py_BuildValue("i", PIN_PC7));
    PyModule_AddObject(module, "PIN2_24", Py_BuildValue("i", PIN_PE9));
    PyModule_AddObject(module, "PIN2_25", Py_BuildValue("i", PIN_PC16));
    PyModule_AddObject(module, "PIN2_26", Py_BuildValue("i", PIN_PE10));
    PyModule_AddObject(module, "PIN2_27", Py_BuildValue("i", PIN_PC17));
    PyModule_AddObject(module, "PIN2_28", Py_BuildValue("i", PIN_PE11));
    PyModule_AddObject(module, "PIN2_29", Py_BuildValue("i", PIN_PC18));
    PyModule_AddObject(module, "PIN2_30", Py_BuildValue("i", PIN_PI14));
    PyModule_AddObject(module, "PIN2_31", Py_BuildValue("i", PIN_PC23));
    PyModule_AddObject(module, "PIN2_32", Py_BuildValue("i", PIN_PI15));
    PyModule_AddObject(module, "PIN2_33", Py_BuildValue("i", PIN_PC24));
    PyModule_AddObject(module, "PIN2_34", Py_BuildValue("i", PIN_PB23));
    PyModule_AddObject(module, "PIN2_36", Py_BuildValue("i", PIN_PB22));

// GPIO-3	
    PyModule_AddObject(module, "PIN3_5", Py_BuildValue("i", PIN_PH0));
    PyModule_AddObject(module, "PIN3_6", Py_BuildValue("i", PIN_PB3));
    PyModule_AddObject(module, "PIN3_7", Py_BuildValue("i", PIN_PH2));
    PyModule_AddObject(module, "PIN3_8", Py_BuildValue("i", PIN_PB4));
    PyModule_AddObject(module, "PIN3_9", Py_BuildValue("i", PIN_PH7));
    PyModule_AddObject(module, "PIN3_10", Py_BuildValue("i", PIN_PB5));
    PyModule_AddObject(module, "PIN3_11", Py_BuildValue("i", PIN_PH9));
    PyModule_AddObject(module, "PIN3_12", Py_BuildValue("i", PIN_PB6));
    PyModule_AddObject(module, "PIN3_13", Py_BuildValue("i", PIN_PH10));
    PyModule_AddObject(module, "PIN3_14", Py_BuildValue("i", PIN_PB7));
    PyModule_AddObject(module, "PIN3_15", Py_BuildValue("i", PIN_PH11));
    PyModule_AddObject(module, "PIN3_16", Py_BuildValue("i", PIN_PB8));
    PyModule_AddObject(module, "PIN3_17", Py_BuildValue("i", PIN_PH12));
    PyModule_AddObject(module, "PIN3_18", Py_BuildValue("i", PIN_PB10));
    PyModule_AddObject(module, "PIN3_19", Py_BuildValue("i", PIN_PH13));
    PyModule_AddObject(module, "PIN3_20", Py_BuildValue("i", PIN_PB11));
    PyModule_AddObject(module, "PIN3_21", Py_BuildValue("i", PIN_PH14));
    PyModule_AddObject(module, "PIN3_22", Py_BuildValue("i", PIN_PB12));
    PyModule_AddObject(module, "PIN3_23", Py_BuildValue("i", PIN_PH15));
    PyModule_AddObject(module, "PIN3_24", Py_BuildValue("i", PIN_PB13));
    PyModule_AddObject(module, "PIN3_25", Py_BuildValue("i", PIN_PH16));
    PyModule_AddObject(module, "PIN3_26", Py_BuildValue("i", PIN_PB14));
    PyModule_AddObject(module, "PIN3_27", Py_BuildValue("i", PIN_PH17));
    PyModule_AddObject(module, "PIN3_28", Py_BuildValue("i", PIN_PB15));
    PyModule_AddObject(module, "PIN3_29", Py_BuildValue("i", PIN_PH18));
    PyModule_AddObject(module, "PIN3_30", Py_BuildValue("i", PIN_PB16));
    PyModule_AddObject(module, "PIN3_31", Py_BuildValue("i", PIN_PH19));
    PyModule_AddObject(module, "PIN3_32", Py_BuildValue("i", PIN_PB17));
    PyModule_AddObject(module, "PIN3_33", Py_BuildValue("i", PIN_PH20));
    PyModule_AddObject(module, "PIN3_34", Py_BuildValue("i", PIN_PH24));
    PyModule_AddObject(module, "PIN3_35", Py_BuildValue("i", PIN_PH21));
    PyModule_AddObject(module, "PIN3_36", Py_BuildValue("i", PIN_PH25));
    PyModule_AddObject(module, "PIN3_37", Py_BuildValue("i", PIN_PH22));
    PyModule_AddObject(module, "PIN3_38", Py_BuildValue("i", PIN_PH26));
    PyModule_AddObject(module, "PIN3_39", Py_BuildValue("i", PIN_PH23));
    PyModule_AddObject(module, "PIN3_40", Py_BuildValue("i", PIN_PH27));

    if(Py_AtExit(sunxi_gpio_cleanup) != 0){
        sunxi_gpio_cleanup();
#if PY_MAJOR_VERSION >= 3
        return NULL;
#else
        return;
#endif
    }



}

