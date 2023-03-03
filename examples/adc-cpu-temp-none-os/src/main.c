#if defined(CH32V00X)
#include <ch32v00x.h>
#elif defined(CH32V10X)
#include <ch32v10x.h>
#elif defined(CH32V20X)
#include <ch32v20x.h>
#elif defined(CH32V30X)
#include <ch32v30x.h>
#endif
#include <stdio.h>
#include "debug.h"

/* Global Variable */
s16 Calibrattion_Val = 0;

void ADC_Function_Init(void)
{
    ADC_InitTypeDef ADC_InitStructure = {0};
    GPIO_InitTypeDef GPIO_InitStructure = {0};

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE);
    RCC_ADCCLKConfig(RCC_PCLK2_Div8);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    ADC_DeInit(ADC1);
    ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;
    ADC_InitStructure.ADC_ScanConvMode = DISABLE;
    ADC_InitStructure.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStructure.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStructure.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &ADC_InitStructure);

    ADC_Cmd(ADC1, ENABLE);
/* V10X does not have the buffer */
#if !defined(CH32V10X)
    ADC_BufferCmd(ADC1, DISABLE); // disable buffer
#endif
    ADC_ResetCalibration(ADC1);
    while (ADC_GetResetCalibrationStatus(ADC1))
        ;
    ADC_StartCalibration(ADC1);
    while (ADC_GetCalibrationStatus(ADC1))
        ;
    Calibrattion_Val = Get_CalibrationValue(ADC1);

#if !defined(CH32V10X)
    ADC_BufferCmd(ADC1, ENABLE); // enable buffer
#endif

    ADC_TempSensorVrefintCmd(ENABLE);
}

u16 Get_ADC_Val(u8 ch)
{
    u16 val;

    ADC_RegularChannelConfig(ADC1, ch, 1, ADC_SampleTime_239Cycles5);
    ADC_SoftwareStartConvCmd(ADC1, ENABLE);

    while (!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC))
        ;

    val = ADC_GetConversionValue(ADC1);

    return val;
}

u16 Get_ADC_Average(u8 ch, u8 times)
{
    u32 temp_val = 0;
    u8 t;
    u16 val;

    for (t = 0; t < times; t++)
    {
        temp_val += Get_ADC_Val(ch);
        Delay_Ms(5);
    }

    val = temp_val / times;

    return val;
}

#if defined(CH32V10X)
u16 Get_ConversionVal_3_3V(s16 val)
{
    int32_t y;
    y = 6 * (val + Calibrattion_Val) / 1000 - 12;
    if (val == 0 || val == 4095)
        return val;
    else
    {
        if ((val + Calibrattion_Val - y) < 0)
            return 0;
        if ((Calibrattion_Val + val - y) > 4095 || val == 4095)
            return 4095;
        return (val + Calibrattion_Val);
    }
}
#endif

u16 Get_ConversionVal(s16 val)
{
    if ((val + Calibrattion_Val) < 0)
        return 0;
    if ((Calibrattion_Val + val) > 4095 || val == 4095)
        return 4095;
    return (val + Calibrattion_Val);
}

int main(void)
{
    u16 ADC_val;
    s32 val_mv;

    SystemCoreClockUpdate();
    Delay_Init();
    USART_Printf_Init(115200);
    Delay_Ms(1000); // give serial monitor time to open
    printf("SystemClk:%u\r\n", (unsigned)SystemCoreClock);
#if defined(CH32V30X)
    printf("ChipID: %08x\r\n", (unsigned)DBGMCU_GetCHIPID());
#else
    printf("DeviceID: %08x\r\n", (unsigned)DBGMCU_GetDEVID());
#endif
    ADC_Function_Init();
    printf("CalibrationValue: %d\n", Calibrattion_Val);

    while (1)
    {
        ADC_val = Get_ADC_Average(ADC_Channel_TempSensor, 10);
        Delay_Ms(500);
#if defined(CH32V10X)
        ADC_val = Get_ConversionVal_3_3V(ADC_val);
#else
        ADC_val = Get_ConversionVal(ADC_val);
#endif
        val_mv = (ADC_val * 3300 / 4096);
        printf("ADC Value: %04d, %ld mV, Temperature: %0ld *C\r\n", ADC_val, val_mv, TempSensor_Volt_To_Temper(val_mv));
        Delay_Ms(2);
    }
    return 0;
}

void NMI_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void NMI_Handler(void) {}
void HardFault_Handler(void) __attribute__((interrupt("WCH-Interrupt-fast")));
void HardFault_Handler(void)
{
    while (1)
    {
    }
}