/******************************************************************************/
/* Files to Include                                                           */
/******************************************************************************/

#include <htc.h>            /* HiTech General Includes */

/******************************************************************************/
/* Configuration Bits                                                         */
/*                                                                            */
/* Refer to 'HI-TECH PICC and PICC18 Toolchains > PICC18 Configuration        */
/* Settings' under Help > Contents in MPLAB X IDE for available PIC18         */
/* Configuration Bit Settings for the correct macros when using the C18       */
/* compiler.  When using the Hi-Tech PICC18 compiler, refer to the compiler   */
/* manual.pdf in the compiler installation doc directory section on           */
/* 'Configuration Fuses'.  The device header file in the HiTech PICC18        */
/* compiler installation directory contains the available macros to be        */
/* embedded.                                                                  */
/*                                                                            */
/* For additional information about what the hardware configurations mean in  */
/* terms of device operation, refer to the device datasheet.                  */
/*                                                                            */
/* General C18 syntax for configuration macros:                               */
/* #pragma config <Macro Name>=<Setting>, <Macro Name>=<Setting>, ...         */
/*                                                                            */
/* General HiTech PICC18 syntax:                                              */
/* __CONFIG(n,x);                                                             */
/*                                                                            */
/* n is the config word number and x represents the anded macros from the     */
/* device header file in the PICC18 compiler installation include directory.  */
/*                                                                            */
/******************************************************************************/

/* TODO Fill in your configuration bits here.  */



__CONFIG(FOSC_INTOSC & WDTE_OFF & PWRTE_OFF & MCLRE_ON & CP_OFF & BOREN_OFF & CLKOUTEN_OFF);
__CONFIG(WRT_OFF & STVREN_OFF & BORV_LO & LPBOR_OFF & LVP_OFF);
