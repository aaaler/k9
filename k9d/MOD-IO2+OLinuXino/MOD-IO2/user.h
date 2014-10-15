/******************************************************************************/
/* User Level #define Macros                                                  */
/******************************************************************************/

#define OLIMEX		0x48
#define MOD_IO2		0x02

#define REL1	LATCbits.LATC4
#define REL2	LATCbits.LATC2
#define REL1_TRIS TRISCbits.TRISC4
#define REL2_TRIS TRISCbits.TRISC2


#define SDA_TRIS TRISCbits.TRISC1
#define SDA_LAT LATCbits.LATC1
#define SDA_PORT PORTCbits.RC1
#define SCL_TRIS TRISCbits.TRISC0
#define SCL_LAT LATCbits.LATC0
#define SCL_PORT PORTCbits.RC0

#define GPIO0_TRIS TRISAbits.TRISA0
#define GPIO0_LAT LATAbits.LATA0
#define GPIO0_PORT PORTAbits.RA0

#define GPIO1_TRIS TRISAbits.TRISA1
#define GPIO1_LAT LATAbits.LATA1
#define GPIO1_PORT PORTAbits.RA1

#define GPIO2_TRIS TRISAbits.TRISA2
#define GPIO2_LAT LATAbits.LATA2
#define GPIO2_PORT PORTAbits.RA2

#define GPIO3_TRIS TRISAbits.TRISA4
#define GPIO3_LAT LATAbits.LATA4
#define GPIO3_PORT PORTAbits.RA4

#define GPIO4_TRIS TRISAbits.TRISA5
#define GPIO4_LAT LATAbits.LATA5
#define GPIO4_PORT PORTAbits.RA5

#define GPIO5_TRIS TRISCbits.TRISC3
#define GPIO5_LAT LATCbits.LATC3
#define GPIO5_PORT PORTCbits.RC3

#define GPIO6_TRIS TRISCbits.TRISC5
#define GPIO6_LAT LATCbits.LATC5
#define GPIO6_PORT PORTCbits.RC5

#define ADDR_MEM	0x700
#define ADDR_DFL	0xA0

#define JMP_TRIS	TRISAbits.TRISA5
#define JMP_LAT		LATAbits.LATA5
#define JMP_PORT	PORTAbits.RA5





#define Nop() asm("NOP")


/******************************************************************************/
/* Local Variables							      */
/******************************************************************************/

extern char ADDRESS;



/******************************************************************************/
/* User Function Prototypes                                                   */
/******************************************************************************/



void InitApp(void);         /* I/O and Peripheral Initialization */
void InitAddress(void);		/* Set the device ID at startup */

/*FLASH MEMORY COMMANDS*/
void WriteFlash(int data, int address);
char ReadFlash(int address);
void EraseFlash(int address);
void UnlockFlash(void);

/*OLIMEX COMMANDS ROUTINES*/
void CommandSetTris(void);
void CommandSetLat(void);
void CommandGetPort(void);
void CommandSetPullUps(void);
void CommandGetAn(char channel);

void CommandSetRelay(void);

void CommandSetAddress(void);


void StartSystem(void);
