/********************************** (C) COPYRIGHT *******************************
 * File Name          : MCU.c
 * Author             : WCH
 * Version            : V1.2
 * Date               : 2022/01/18
 * Description        : HAL task processing function and BLE and hardware initialization
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/******************************************************************************/
/* Header file contains */
#include "HAL.h"
#include "string.h"
#include "debug.h"

tmosTaskID halTaskID;

/*******************************************************************************
 * @fn      Lib_Calibration_LSI
 *
 * @brief   Internal 32K calibration
 *
 * @param   None.
 *
 * @return  None.
 */
void Lib_Calibration_LSI(void)
{
    Calibration_LSI(Level_64);
}

#if(defined(BLE_SNV)) && (BLE_SNV == TRUE)
/*******************************************************************************
 * @fn      Lib_Read_Flash
 *
 * @brief   Callback function used for BLE lib.
 *
 * @param   addr.
 * @param   num.
 * @param   pBuf.
 *
 * @return  None.
 */
uint32_t Lib_Read_Flash(uint32_t addr, uint32_t num, uint32_t *pBuf)
{
    tmos_memcpy(pBuf, (uint32_t*)addr, num*4);
    return 0;
}

/*******************************************************************************
 * @fn      Lib_Write_Flash
 *
 * @brief   Callback function used for BLE lib.
 *
 * @param   addr.
 * @param   num.
 * @param   pBuf.
 *
 * @return  None.
 */
uint32_t Lib_Write_Flash(uint32_t addr, uint32_t num, uint32_t *pBuf)
{
    FLASH_Unlock_Fast();
    FLASH_ErasePage_Fast( addr );
    FLASH_ProgramPage_Fast( addr, pBuf);
    FLASH_Lock_Fast();
    Delay_Us(1);
    return 0;
}
#endif

/*******************************************************************************
 * @fn      WCHBLE_Init
 *
 * @brief   BLE library initialization
 *
 * @param   None.
 *
 * @return  None.
 */
void WCHBLE_Init(void)
{
    uint8_t     i;
    bleConfig_t cfg;
    if(!tmos_memcmp(VER_LIB, VER_FILE, strlen(VER_FILE)))
    {
        PRINT("head file error...\n");
        while(1);
    }

    // 32M crystal capacitance and current
    OSC->HSE_CAL_CTRL &= ~(0x07<<28);
    OSC->HSE_CAL_CTRL |= 0x03<<28;
    OSC->HSE_CAL_CTRL |= 3<<24;

    tmos_memset(&cfg, 0, sizeof(bleConfig_t));
    cfg.MEMAddr = (uint32_t)MEM_BUF;
    cfg.MEMLen = (uint32_t)BLE_MEMHEAP_SIZE;
    cfg.BufMaxLen = (uint32_t)BLE_BUFF_MAX_LEN;
    cfg.BufNumber = (uint32_t)BLE_BUFF_NUM;
    cfg.TxNumEvent = (uint32_t)BLE_TX_NUM_EVENT;
    cfg.TxPower = (uint32_t)BLE_TX_POWER;
#if(defined(BLE_SNV)) && (BLE_SNV == TRUE)
    cfg.SNVAddr = (uint32_t)BLE_SNV_ADDR;
    cfg.SNVNum = (uint32_t)BLE_SNV_NUM;
    cfg.readFlashCB = Lib_Read_Flash;
    cfg.writeFlashCB = Lib_Write_Flash;
#endif
    cfg.ClockFrequency = CAB_LSIFQ/2;
#if(CLK_OSC32K==0)
    cfg.ClockAccuracy = 50;
#else
    cfg.ClockAccuracy = 1000;
#endif
    cfg.ConnectNumber = (PERIPHERAL_MAX_CONNECTION & 3) | (CENTRAL_MAX_CONNECTION << 2);
#if(defined TEM_SAMPLE) && (TEM_SAMPLE == TRUE)
    // Calibrate RF and internal RC according to temperature changes (greater than 7 degrees Celsius)
    cfg.tsCB = HAL_GetInterTempValue;
  #if(CLK_OSC32K)
    cfg.rcCB = Lib_Calibration_LSI; // Internal 32K clock calibration
  #endif
#endif
#if(defined(HAL_SLEEP)) && (HAL_SLEEP == TRUE)
    cfg.idleCB = BLE_LowPower; // Enable sleep
#endif
#if(defined(BLE_MAC)) && (BLE_MAC == TRUE)
    for(i = 0; i < 6; i++)
    {
        cfg.MacAddr[i] = MacAddr[5 - i];
    }
#else
    {
        uint8_t MacAddr[6];
        FLASH_GetMACAddress(MacAddr);
        for(i = 0; i < 6; i++)
        {
            cfg.MacAddr[i] = MacAddr[i]; // Use chip mac address
        }
    }
#endif
    if(!cfg.MEMAddr || cfg.MEMLen < 4 * 1024)
    {
        while(1);
    }
    i = BLE_LibInit(&cfg);
    if(i)
    {
        PRINT("LIB init error code: %x ...\n", i);
        while(1);
    }
    RCC_AHBPeriphClockCmd(RCC_AHBPeriph_CRC, ENABLE );
    NVIC_EnableIRQ( BB_IRQn );
    NVIC_EnableIRQ( LLE_IRQn );
}

/*******************************************************************************
 * @fn      HAL_ProcessEvent
 *
 * @brief   HAL processing
 *
 * @param   task_id - The TMOS assigned task ID.
 * @param   events  - events to process.  This is a bit map and can
 *                      contain more than one event.
 *
 * @return  events.
 */
tmosEvents HAL_ProcessEvent(tmosTaskID task_id, tmosEvents events)
{
    uint8_t *msgPtr;

    if(events & SYS_EVENT_MSG)
    { 
        /**
         * Process the HAL layer message, call tmos_msg_receive to read the message, 
         * and delete the message after processing.
         */
        msgPtr = tmos_msg_receive(task_id);
        if(msgPtr)
        {
            /* De-allocate */
            tmos_msg_deallocate(msgPtr);
        }
        return events ^ SYS_EVENT_MSG;
    }
    if(events & LED_BLINK_EVENT)
    {
#if(defined HAL_LED) && (HAL_LED == TRUE)
        HalLedUpdate();
#endif // HAL_LED
        return events ^ LED_BLINK_EVENT;
    }
    if(events & HAL_KEY_EVENT)
    {
#if(defined HAL_KEY) && (HAL_KEY == TRUE)
        HAL_KeyPoll(); /* Check for keys */
        tmos_start_task(halTaskID, HAL_KEY_EVENT, MS1_TO_SYSTEM_TIME(100));
        return events ^ HAL_KEY_EVENT;
#endif
    }
    if(events & HAL_REG_INIT_EVENT)
    {
#if(defined BLE_CALIBRATION_ENABLE) && (BLE_CALIBRATION_ENABLE == TRUE) // Calibration tasks, a single time is less than 10ms
        BLE_RegInit();                                                  // Calibrate RF
#if(CLK_OSC32K)
        Lib_Calibration_LSI(); // Calibrate internal RC
#endif
        tmos_start_task(halTaskID, HAL_REG_INIT_EVENT, MS1_TO_SYSTEM_TIME(BLE_CALIBRATION_PERIOD));
        return events ^ HAL_REG_INIT_EVENT;
#endif
    }
    if(events & HAL_TEST_EVENT)
    {
        PRINT("* \n");
        tmos_start_task(halTaskID, HAL_TEST_EVENT, MS1_TO_SYSTEM_TIME(1000));
        return events ^ HAL_TEST_EVENT;
    }
    return 0;
}

/*******************************************************************************
 * @fn      HAL_Init
 *
 * @brief   Ӳ����ʼ��
 *
 * @param   None.
 *
 * @return  None.
 */
void HAL_Init()
{
    halTaskID = TMOS_ProcessEventRegister(HAL_ProcessEvent);
    HAL_TimeInit();
#if(defined HAL_SLEEP) && (HAL_SLEEP == TRUE)
    HAL_SleepInit();
#endif
#if(defined HAL_LED) && (HAL_LED == TRUE)
    HAL_LedInit();
#endif
#if(defined HAL_KEY) && (HAL_KEY == TRUE)
    HAL_KeyInit();
#endif
#if(defined BLE_CALIBRATION_ENABLE) && (BLE_CALIBRATION_ENABLE == TRUE)
    // Add a calibration task, and a single calibration takes less than 10ms
    tmos_start_task(halTaskID, HAL_REG_INIT_EVENT, MS1_TO_SYSTEM_TIME(BLE_CALIBRATION_PERIOD)); 
#endif
//    tmos_start_task(halTaskID, HAL_TEST_EVENT, MS1_TO_SYSTEM_TIME(1000));    // Add a test task
}

/*******************************************************************************
 * @fn      HAL_GetInterTempValue
 *
 * @brief   Get the internal temperature sampling value, if the ADC interrupt sampling is used, 
 *          it is necessary to temporarily shield the interrupt in this function.
 *
 * @return  Internal temperature sampling value.
 */
uint16_t HAL_GetInterTempValue(void)
{
    uint32_t rcc_apb2pcenr, rcc_cfgr0, adc1_ctrl1, adc1_ctrl2, adc1_rsqr1, adc1_rsqr3, adc1_samptr1;
    ADC_InitTypeDef  ADC_InitStructure = {0};
    uint16_t adc_data;

    rcc_apb2pcenr = RCC->APB2PCENR;
    rcc_cfgr0 = RCC->CFGR0;
    adc1_ctrl1 = ADC1->CTLR1;
    adc1_ctrl2 = ADC1->CTLR2;
    adc1_rsqr1 = ADC1->RSQR1;
    adc1_rsqr3 = ADC1->RSQR3;
    adc1_samptr1 = ADC1->SAMPTR1;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE);
    RCC_ADCCLKConfig(RCC_PCLK2_Div8);
    ADC_DeInit(ADC1);
    ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;
    ADC_InitStructure.ADC_ScanConvMode = DISABLE;
    ADC_InitStructure.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStructure.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStructure.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &ADC_InitStructure);

    ADC_Cmd(ADC1, ENABLE);
    ADC_BufferCmd(ADC1, ENABLE); //enable buffer
    ADC_TempSensorVrefintCmd(ENABLE);
    ADC_RegularChannelConfig(ADC1, ADC_Channel_TempSensor, 1, ADC_SampleTime_239Cycles5);
    ADC_SoftwareStartConvCmd(ADC1, ENABLE);
    while(!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC));
    adc_data = ADC_GetConversionValue(ADC1);

    ADC_DeInit(ADC1);
    RCC->APB2PCENR = rcc_apb2pcenr;
    RCC->CFGR0 = rcc_cfgr0;
    ADC1->CTLR1 = adc1_ctrl1;
    ADC1->CTLR2 = adc1_ctrl2;
    ADC1->RSQR1 = adc1_rsqr1;
    ADC1->RSQR3 = adc1_rsqr3;
    ADC1->SAMPTR1 = adc1_samptr1;
    return (adc_data);
}

/******************************** endfile @ mcu ******************************/
