#include <LPC213x.h>

/*
 * ============================================================
 * LPC2138 Virtual IoT Temperature Sensor
 * ============================================================
 *
 * MCU:
 *     LPC2138
 *
 * Simulation:
 *     Proteus
 *
 * Sensor:
 *     LM35
 *
 * ADC:
 *     AD0.0
 *     P0.27
 *     Pin 10
 *
 * UART:
 *     UART0
 *     TXD0 = P0.0 = Pin 19
 *     RXD0 = P0.1 = Pin 21
 *
 * UART configuration:
 *     9600 baud
 *     8 data bits
 *     No parity
 *     1 stop bit
 *
 * Crystal:
 *     12 MHz
 *
 * PCLK:
 *     12 MHz
 *
 * LM35:
 *     10 mV / degree Celsius
 *
 * ============================================================
 */


/* ------------------------------------------------------------
 * Configuration
 * ------------------------------------------------------------ */

#define PCLK           12000000UL
#define BAUD_RATE      9600UL

#define DEVICE_ID      "LPC2138-TEMP-001"
#define DEVICE_TYPE    "TEMPERATURE_SENSOR"
#define FIRMWARE_VER   "1.0.0"


/* ------------------------------------------------------------
 * Simple delay
 * ------------------------------------------------------------ */

void delay(void)
{
    volatile unsigned long i;

    for (i = 0; i < 100000; i++)
    {
        /* delay */
    }
}


/* ------------------------------------------------------------
 * UART0 Initialization
 * ------------------------------------------------------------ */

void UART0_Init(void)
{
    /*
     * P0.0 = TXD0
     * P0.1 = RXD0
     */
    PINSEL0 &= ~0x0000000FUL;
    PINSEL0 |=  0x00000005UL;


    /*
     * Peripheral clock = CCLK
     *
     * VPBDIV = 01
     *
     * Therefore:
     *
     * PCLK = 12 MHz
     */
    VPBDIV = 0x01;


    /*
     * UART configuration
     *
     * 8 data bits
     * 1 stop bit
     * No parity
     *
     * DLAB = 1
     */
    U0LCR = 0x83;


    /*
     * Baud rate:
     *
     * PCLK = 12 MHz
     * Baud = 9600
     *
     * Divisor ˜ 78
     */
    U0DLL = 78;
    U0DLM = 0;


    /*
     * Disable divisor latch access
     */
    U0LCR = 0x03;
}


/* ------------------------------------------------------------
 * UART Send Character
 * ------------------------------------------------------------ */

void UART0_SendChar(char c)
{
    /*
     * Wait until THR is empty
     */
    while (!(U0LSR & 0x20))
    {
    }

    U0THR = c;
}


/* ------------------------------------------------------------
 * UART Send String
 * ------------------------------------------------------------ */

void UART0_SendString(const char *str)
{
    while (*str)
    {
        UART0_SendChar(*str);
        str++;
    }
}


/* ------------------------------------------------------------
 * UART Send Unsigned Integer
 * ------------------------------------------------------------ */

void UART0_SendNumber(unsigned int value)
{
    char buffer[10];

    int i = 0;


    /*
     * Special case for zero
     */
    if (value == 0)
    {
        UART0_SendChar('0');
        return;
    }


    /*
     * Convert number to characters
     */
    while (value > 0)
    {
        buffer[i++] = (char)((value % 10) + '0');

        value /= 10;
    }


    /*
     * Send characters in reverse order
     */
    while (i > 0)
    {
        UART0_SendChar(buffer[--i]);
    }
}


/* ------------------------------------------------------------
 * ADC0 Initialization
 * ------------------------------------------------------------ */

void ADC0_Init(void)
{
    /*
     * P0.27 = AD0.0
     *
     * P0.27 pin function is selected
     * through PINSEL1 bits 22:21.
     *
     * 01 = AD0.0
     */

    PINSEL1 &= ~(3UL << 22);

    PINSEL1 |= (1UL << 22);


    /*
     * Clear ADC configuration
     */
    AD0CR = 0;


    /*
     * Select ADC channel 0
     */
    AD0CR |= (1UL << 0);


    /*
     * ADC clock divider
     *
     * PCLK = 12 MHz
     *
     * ADC clock:
     *
     * 12 MHz / (2 + 1)
     * = 4 MHz
     */
    AD0CR |= (2UL << 8);


    /*
     * Power up ADC
     */
    AD0CR |= (1UL << 21);
}


/* ------------------------------------------------------------
 * ADC0 Read
 * ------------------------------------------------------------ */

unsigned int ADC0_Read(void)
{
    unsigned long data;


    /*
     * Select channel 0
     */
    AD0CR &= ~0x000000FFUL;

    AD0CR |= 0x01UL;


    /*
     * Start conversion
     *
     * START bits = 001
     */
    AD0CR &= ~(7UL << 24);

    AD0CR |= (1UL << 24);


    /*
     * Wait for conversion complete
     */
    do
    {
        data = AD0GDR;

    } while (!(data & (1UL << 31)));


    /*
     * Stop conversion
     */
    AD0CR &= ~(7UL << 24);


    /*
     * ADC result:
     *
     * Bits 6-15
     *
     * 10-bit result
     */
    return (unsigned int)((data >> 6) & 0x3FFUL);
}


/* ------------------------------------------------------------
 * Convert ADC value to LM35 temperature
 * ------------------------------------------------------------ */

unsigned int ADC_To_Temperature(unsigned int adc_value)
{
    /*
     * LPC2138 ADC reference:
     *
     * VREF = 3.3V
     *
     * ADC resolution:
     *
     * 10 bits = 1023
     *
     *
     * ADC voltage:
     *
     *     V = ADC × 3.3 / 1023
     *
     *
     * LM35:
     *
     *     10mV / °C
     *
     * Therefore:
     *
     *     Temperature = V × 100
     *
     *
     * Combining:
     *
     *     Temperature =
     *         ADC × 3.3 × 100 / 1023
     *
     *     Temperature =
     *         ADC × 330 / 1023
     */

    return (unsigned int)
           ((adc_value * 330UL) / 1023UL);
}


/* ------------------------------------------------------------
 * Send Device Startup Message
 * ------------------------------------------------------------ */

void Send_Device_Startup(void)
{
    UART0_SendString("\r\n");

    UART0_SendString("================================\r\n");

    UART0_SendString("VIRTUAL IOT DEVICE STARTED\r\n");

    UART0_SendString("DEVICE_ID=");
    UART0_SendString(DEVICE_ID);
    UART0_SendString("\r\n");

    UART0_SendString("TYPE=");
    UART0_SendString(DEVICE_TYPE);
    UART0_SendString("\r\n");

    UART0_SendString("FIRMWARE=");
    UART0_SendString(FIRMWARE_VER);
    UART0_SendString("\r\n");

    UART0_SendString("SENSOR=LM35\r\n");

    UART0_SendString("================================\r\n");
}


/* ------------------------------------------------------------
 * Send Heartbeat
 * ------------------------------------------------------------ */

void Send_Heartbeat(unsigned int sequence)
{
    UART0_SendString("HEARTBEAT");

    UART0_SendString(";DEVICE_ID=");
    UART0_SendString(DEVICE_ID);

    UART0_SendString(";SEQ=");
    UART0_SendNumber(sequence);

    UART0_SendString("\r\n");
}


/* ------------------------------------------------------------
 * Send Temperature Telemetry
 * ------------------------------------------------------------ */

void Send_Telemetry(unsigned int sequence,
                    unsigned int adc_value,
                    unsigned int temperature)
{
    UART0_SendString("TELEMETRY");

    UART0_SendString(";DEVICE_ID=");
    UART0_SendString(DEVICE_ID);

    UART0_SendString(";TYPE=");
    UART0_SendString(DEVICE_TYPE);

    UART0_SendString(";SEQ=");
    UART0_SendNumber(sequence);

    UART0_SendString(";ADC=");
    UART0_SendNumber(adc_value);

    UART0_SendString(";TEMP=");
    UART0_SendNumber(temperature);

    UART0_SendString("\r\n");
}


/* ------------------------------------------------------------
 * Main
 * ------------------------------------------------------------ */

int main(void)
{
    unsigned int adc_value;

    unsigned int temperature;

    unsigned int sequence = 1;


    /*
     * Initialize UART
     */
    UART0_Init();


    /*
     * Initialize ADC
     */
    ADC0_Init();


    /*
     * Send startup information
     */
    Send_Device_Startup();


    /*
     * Main device loop
     */
    while (1)
    {
        /*
         * Read LM35
         */
        adc_value = ADC0_Read();


        /*
         * Convert ADC value to temperature
         */
        temperature = ADC_To_Temperature(adc_value);


        /*
         * Send telemetry
         */
        Send_Telemetry(
            sequence,
            adc_value,
            temperature
        );


        /*
         * Every 10 telemetry messages,
         * send a heartbeat.
         */
        if ((sequence % 10) == 0)
        {
            Send_Heartbeat(sequence);
        }


        /*
         * Increment sequence number
         */
        sequence++;


        /*
         * Wait
         */
        delay();
    }
}
