/******************************************************************************/
/* Files to Include                                                           */
/******************************************************************************/

#include <htc.h>            /* HiTech General Includes */
#include <stdint.h>         /* For uint8_t definition */
#include <stdbool.h>        /* For true/false definition */

#include "user.h"
#include "i2c.h"
#include "OLIMEX.h"

/******************************************************************************/
/* User Functions                                                             */
/******************************************************************************/

/* <Initialize variables in user.h and insert code for user algorithms.> */

void InitApp(void)
{
    /* TODO Initialize User Ports/Peripherals/Project here */

    /* Setup analog functionality and port direction */
	ANSELC = 0x00;
	ANSELA = 0x00;

	SCL_TRIS = 1;
	SDA_TRIS = 1;
	SCL_LAT = 0;
	SDA_LAT = 0;

	REL1_TRIS = 0;
	REL2_TRIS = 0;
	REL1 = 0;
	REL2 = 0;

	OPTION_REGbits.nWPUEN = 0;
	WPUAbits.WPUA = 0;
	WPUAbits.WPUA5 = 1;
	JMP_TRIS = 1;
	JMP_LAT = 0;




    /* Initialize peripherals */

    /* Enable interrupts */
}
void InitAddress(void)
{
	char address;
	/* READ THE JUMPER*/
	JMP_TRIS = 1;
	WPUAbits.WPUA5 = 1;
	if(!JMP_PORT)
	{
		/* SET ADDRESS FOR PROGRAMMING*/
		ADDRESS = 0xF0;
	}
	else
	{
		address = ReadFlash(ADDR_MEM);
		/* IF THE MEMORY CELL IS EMPTY*/
		if (address == 0xFF)
			ADDRESS = ADDR_DFL;
		else
			ADDRESS = address;
	}
}
char ReadFlash(int address)
{
	char data = 0;
	PMADRL = address & 0x00FF;
	address >>= 8;
	PMADRH = address & 0x00FF;
	PMCON1bits.CFGS = 0;
	PMCON1bits.RD = 1;
	Nop();
	Nop();

	data = PMDATL;
	return data;
}
void EraseFlash(int address)
{
	GIE = 0;
	PMADRL = address & 0x00FF;
	address >>= 8;
	PMADRH = address & 0x00FF;
	PMCON1bits.CFGS = 0;
	PMCON1bits.FREE = 1;
	PMCON1bits.WREN = 1;
	UnlockFlash();
	PMCON1bits.WREN = 0;
	GIE = 1;
}
void UnlockFlash(void)
{
	PMCON2 = 0x55;
	PMCON2 = 0xAA;
	PMCON1bits.WR = 1;
	Nop();
	Nop();
}
void WriteFlash(int data, int address)
{
	GIE = 0;
	PMCON1bits.CFGS = 0;
	PMADRL = address & 0x00FF;
	address >>= 8;
	PMADRH = address & 0x00FF;
	PMCON1bits.FREE = 0;
	PMCON1bits.LWLO = 1;
	PMCON1bits.WREN = 1;
	PMDATL = data & 0x00FF;
	data >>= 8;
	PMDATH = data & 0x00FF;
	PMCON1bits.LWLO = 0;
	UnlockFlash();
	PMCON1bits.WREN = 0;
	GIE = 1;
}
void CommandSetTris()
{
	char data;
	data = ReadByteI2C();
	SendAck();


	GPIO0_TRIS = data & 0x01;
	data >>= 1;
	GPIO1_TRIS = data & 0x01;
	data >>= 1;
	GPIO2_TRIS = data & 0x01;
	data >>= 1;
	GPIO3_TRIS = 1;
	data >>= 1;
	GPIO4_TRIS = data & 0x01;
	data >>= 1;
	GPIO5_TRIS = data & 0x01;
	data >>= 1;
	GPIO6_TRIS = data & 0x01;

}
void CommandSetLat()
{

	char data;
	data = ReadByteI2C();
	SendAck();


	GPIO0_LAT = data & 0x01;
	data >>= 1;
	GPIO1_LAT = data & 0x01;
	data >>= 1;
	GPIO2_LAT = data & 0x01;
	data >>= 1;
//	GPIO3_LAT = command & 0x01;	GPIO3 is ALWAYS INPUT!!!
	data >>= 1;
	GPIO4_LAT = data & 0x01;
	data >>= 1;
	GPIO5_LAT = data & 0x01;
	data >>= 1;
	GPIO6_LAT = data & 0x01;

}
void CommandGetPort()
{
	char company;
	char data;
	StopI2C();
	StartI2C();
	company = ReadByteI2C();
	company >>= 1;
	if (company == OLIMEX)
	{
		SendAck();

		data = GPIO6_PORT & 0x01;
		data <<= 1;
		data |= GPIO5_PORT & 0x01;
		data <<= 1;
		data |= GPIO4_PORT & 0x01;
		data <<= 1;
		data |= GPIO3_PORT & 0x01;
		data <<= 1;
		data |= GPIO2_PORT & 0x01;
		data <<= 1;
		data |= GPIO1_PORT & 0x01;
		data <<= 1;
		data |= GPIO0_PORT & 0x01;

		WriteByteI2C(data);

	}
	else
		SendNack();

}
void CommandSetRelay()
{
	
	char data;
	data = ReadByteI2C();
	SendAck();



	REL1 = data & 0x01;
	data >>= 1;
	REL2 = data & 0x01;
	data >>= 1;
}
void CommandSetAddress()
{

	char address;
	address = ReadByteI2C();
	SendAck();



	/* STORE THE NEW ADDRESS INTO THE FLASH MEMORY */
	EraseFlash(ADDR_MEM);
	WriteFlash(address, ADDR_MEM);
	ADDRESS = address;
}
void CommandSetPullUps()
{
	char data;
	data = ReadByteI2C();
	SendAck();

	WPUAbits.WPUA0 = data & 0x01;
	data >>= 1;
	WPUAbits.WPUA1 = data & 0x01;
	data >>= 1;
	WPUAbits.WPUA2 = data & 0x01;
	data >>= 1;
	WPUAbits.WPUA3 = data & 0x01;
	data >>= 1;
	WPUAbits.WPUA5 = data & 0x01;
	data >>= 1;

}

void CommandGetAn(char channel)
{
	long int result;

	/* PORT INIT */

	char company;
	StopI2C();
	
	switch(channel)
	{
	case 0:
	{
		TRISAbits.TRISA0 = 1;
		ANSELAbits.ANSA0 = 1;
	} break;
	case 1:
	{
		TRISAbits.TRISA1 = 1;
		ANSELAbits.ANSA1 = 1;
	} break;
	case 2:
	{
		TRISAbits.TRISA2 = 1;
		ANSELAbits.ANSA2 = 1;
	} break;
	case 3:
	{
		TRISAbits.TRISA4 = 1;
		ANSELAbits.ANSA4 = 1;
	} break;
	case 7:
	{
		TRISCbits.TRISC3 = 1;
		ANSELCbits.ANSC3 = 1;
	} break;


	default: break;
	}


	/*CONFIG ADC*/
	ADCON1bits.ADFM = 1;
	ADCON1bits.ADCS = 0;
	ADCON1bits.ADPREF = 0;
	ADCON0bits.CHS = channel;
	ADCON0bits.ADON = 1;

	ADCON0bits.ADGO = 1;
	while(ADCON0bits.ADGO) ;

	result = ADRESH;
	result << = 8;
	result |= ADRESL;

	StartI2C();
	company = ReadByteI2C();
	company >>= 1;
	if (company == OLIMEX)
	{
		SendAck();
		WriteWordI2C(result);
	}
	else
		SendNack();

}



void StartSystem(void)
{
    unsigned char company, device, address, command;

    /*Loop until START condition is recieved*/
    StartI2C();

    /*Read the first bit of the address*/
    company = ReadByteI2C();
    company >>= 1;
    

    if (company == OLIMEX)
    {
	    SendAck();

	    /*Read the second bit of the address*/
	    device = ReadByteI2C();
	    if (device == MOD_IO2)
	    {
		    SendAck();
 
		    /*Read the third bit of the address*/
		    address = ReadByteI2C();
		    if(ADDRESS == address)
		    {
			 
			   
			    SendAck();

			    command = ReadByteI2C();
			    SendAck();
			    
			    if(SET_REL == command)
				    CommandSetRelay();
			    else if(SET_ADDRESS == command)
				    CommandSetAddress();				    
			    else if(SET_TRIS == command)
				    CommandSetTris();				   
			    else if(SET_LAT == command)
				    CommandSetLat();
			    else if(GET_PORT == command)
				    CommandGetPort();
			    else if(SET_PU == command)
				   CommandSetPullUps();
			    else if(GET_AN0 == command)
				    CommandGetAn(0);
			    else if(GET_AN1 == command)
				    CommandGetAn(1);
			    else if(GET_AN2 == command)
				    CommandGetAn(2);
			    else if(GET_AN3 == command)
				    CommandGetAn(3);
			    else if(GET_AN7 == command)
				    CommandGetAn(7);
			    else
				    SendNack();

		    }
		    else
			    SendNack();
	    }
	    else
		    SendNack();

    }
    else
	    SendNack();
    /*Wait for STOP condition*/
    StopI2C();


    }

