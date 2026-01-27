/********************************** (C) COPYRIGHT *******************************
* File Name          : eth_driver.c
* Author             : WCH
* Version            : V1.0.0
* Date               : 2026/01/14
* Description        : eth program body.
*********************************************************************************
* Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
* Attention: This software (modified or not) and binary are used for 
* microcontroller manufactured by Nanjing Qinheng Microelectronics.
*******************************************************************************/

#include "string.h"
#include "eth_driver.h"

__attribute__((__aligned__(32))) ETH_DMADESCTypeDef DMARxDscrTab[ETH_RXBUFNB];       /* MAC receive descriptor, 4-byte aligned*/
__attribute__((__aligned__(32))) ETH_DMADESCTypeDef DMATxDscrTab[ETH_TXBUFNB];       /* MAC send descriptor, 4-byte aligned */

__attribute__((__aligned__(4))) uint8_t  MACRxBuf[ETH_RXBUFNB*ETH_RX_BUF_SZE];      /* MAC receive buffer, 4-byte aligned */
__attribute__((__aligned__(4))) uint8_t  MACTxBuf[ETH_TXBUFNB*ETH_TX_BUF_SZE];      /* MAC send buffer, 4-byte aligned */

__attribute__((__aligned__(4))) SOCK_INF SocketInf[WCHNET_MAX_SOCKET_NUM];          /* Socket information table, 4-byte alignment */
const uint16_t MemNum[8] = {WCHNET_NUM_IPRAW,
                         WCHNET_NUM_UDP,
                         WCHNET_NUM_TCP,
                         WCHNET_NUM_TCP_LISTEN,
                         WCHNET_NUM_TCP_SEG,
                         WCHNET_NUM_IP_REASSDATA,
                         WCHNET_NUM_PBUF,
                         WCHNET_NUM_POOL_BUF
                         };
const uint16_t MemSize[8] = {WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_IPRAW_PCB),
                          WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_UDP_PCB),
                          WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_TCP_PCB),
                          WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_TCP_PCB_LISTEN),
                          WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_TCP_SEG),
                          WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_IP_REASSDATA),
                          WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_PBUF),
                          WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_PBUF) + WCHNET_MEM_ALIGN_SIZE(WCHNET_SIZE_POOL_BUF)
                         };
__attribute__((__aligned__(4)))uint8_t Memp_Memory[WCHNET_MEMP_SIZE];
__attribute__((__aligned__(4)))uint8_t Mem_Heap_Memory[WCHNET_RAM_HEAP_SIZE];
__attribute__((__aligned__(4)))uint8_t Mem_ArpTable[WCHNET_RAM_ARP_TABLE_SIZE];

uint16_t gPHYAddress;
uint32_t volatile LocalTime;

ETH_DMADESCTypeDef *pDMARxSet;
ETH_DMADESCTypeDef *pDMATxSet;

#if !LINK_STAT_ACQUISITION_METHOD
u16 LastPhyStat = 0;
u32 LastQueryPhyTime = 0;
#endif

/*********************************************************************
 * @fn      WCHNET_GetMacAddr
 *
 * @brief   Get the MAC address
 *
 * @return  none.
 */
void WCHNET_GetMacAddr( uint8_t *p )
{
    uint8_t i;
    uint8_t *macaddr=(uint8_t *)(ROM_CFG_USERADR_ID+5);

    for(i=0;i<6;i++)
    {
        *p = *macaddr;
        p++;
        macaddr--;
    }
}

/*********************************************************************
 * @fn      WCHNET_TimeIsr
 *
 * @brief
 *
 * @return  none.
 */
void WCHNET_TimeIsr( uint16_t timperiod )
{
    LocalTime += timperiod;
}

/*********************************************************************
 * @fn      WCHNET_QueryPhySta
 *
 * @brief   Query external PHY status
 *
 * @return  none.
 */
#if !LINK_STAT_ACQUISITION_METHOD
void WCHNET_QueryPhySta(void)
{
    u16 phy_stat;
    if(QUERY_STAT_FLAG){                                         /* Query the PHY link status every 1s */
        LastQueryPhyTime = LocalTime / 1000;
        ETH_WritePHYRegister( PHY_ADDRESS, 0x1F, 0x0a43 );
        /*In some cases the status is not updated in time,
         * so read this register twice to get the correct status value.*/
        ETH_ReadPHYRegister( PHY_ADDRESS, 0x1A);
        phy_stat = ETH_ReadPHYRegister( PHY_ADDRESS, 0x1A) & 0x04;
        if((phy_stat != LastPhyStat) && (phy_stat != 0xffff)){
            ETH_PHYLink();
        }
    }
}
#endif

/*********************************************************************
 * @fn      WCHNET_MainTask
 *
 * @brief   library main task function
 *
 * @param   none.
 *
 * @return  none.
 */
void WCHNET_MainTask(void)
{
    WCHNET_NetInput( );                     /* Ethernet data input */
    WCHNET_PeriodicHandle( );               /* Protocol stack time-related task processing */

#if !LINK_STAT_ACQUISITION_METHOD
    WCHNET_QueryPhySta();                   /* Query external PHY status */
#endif
}

/*********************************************************************
 * @fn      ETH_RGMIIPinInit
 *
 * @brief   PHY RGMII interface GPIO initialization.
 *
 * @param   none.
 *
 * @return  none.
 */
void ETH_RGMIIPinInit(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_HB2PeriphClockCmd(RCC_HB2Periph_AFIO | RCC_HB2Periph_GPIOA|\
                            RCC_HB2Periph_GPIOC | RCC_HB2Periph_GPIOD, ENABLE);
    
    GPIO_PinAFConfig(GPIOD, GPIO_PinSource15, GPIO_AF10);    //GTXC
    GPIO_Output(GPIOD, GPIO_Pin_15);

    GPIO_PinAFConfig(GPIOA, GPIO_PinSource14, GPIO_AF12);    //RXDV
    GPIO_Input(GPIOA, GPIO_Pin_14);

    GPIO_PinAFConfig(GPIOA, GPIO_PinSource15, GPIO_AF3);    //RXC
    GPIO_Input(GPIOA, GPIO_Pin_15);

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource6, GPIO_AF12);    //RXD3
    GPIO_Input(GPIOC, GPIO_Pin_6);

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource8, GPIO_AF12);    //RXD1
    GPIO_Input(GPIOC, GPIO_Pin_8);

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource9, GPIO_AF12);    //RXD0
    GPIO_Input(GPIOC, GPIO_Pin_9);

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource7, GPIO_AF12);    //RXD2
    GPIO_Input(GPIOC, GPIO_Pin_7);

    GPIO_PinAFConfig(GPIOD, GPIO_PinSource13, GPIO_AF10);    //TXD0
    GPIO_Output(GPIOD, GPIO_Pin_13);

    GPIO_PinAFConfig(GPIOD, GPIO_PinSource12, GPIO_AF10);    //TXD1
    GPIO_Output(GPIOD, GPIO_Pin_12);

    GPIO_PinAFConfig(GPIOD, GPIO_PinSource11, GPIO_AF10);    //TXD2
    GPIO_Output(GPIOD, GPIO_Pin_11);

    GPIO_PinAFConfig(GPIOD, GPIO_PinSource10, GPIO_AF10);    //TXD3
    GPIO_Output(GPIOD, GPIO_Pin_10);

    GPIO_PinAFConfig(GPIOD, GPIO_PinSource14, GPIO_AF10);    //TXEN
    GPIO_Output(GPIOD, GPIO_Pin_14);

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource0, GPIO_AF1);    //MDC
    GPIO_Output(GPIOC, GPIO_Pin_0);

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource1, GPIO_AF1);    //MDIO
    GPIO_Output(GPIOC, GPIO_Pin_1);
}

#if LINK_STAT_ACQUISITION_METHOD
/*********************************************************************
 * @fn      EXTI_Line_Init
 *
 * @brief   Configure EXTI Line7.
 *
 * @param   none.
 *
 * @return  none.
 */
void EXTI_Line_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStructure = {0};
    EXTI_InitTypeDef EXTI_InitStructure = {0};

    RCC_HB2PeriphClockCmd(RCC_HB2Periph_AFIO | RCC_HB2Periph_GPIOB, ENABLE);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_13;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    /* GPIOC 7 ----> EXTI_Line7 */
    GPIO_EXTILineConfig(GPIO_PortSourceGPIOB, GPIO_PinSource13);
    EXTI_InitStructure.EXTI_Line = EXTI_Line13;
    EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
    EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling;
    EXTI_InitStructure.EXTI_LineCmd = ENABLE;
    EXTI_Init(&EXTI_InitStructure);

    NVIC_SetPriority(EXTI15_8_IRQn,ENABLE);
    NVIC_EnableIRQ(EXTI15_8_IRQn);
}

/*********************************************************************
 * @fn      PHY_InterruptInit
 *
 * @brief   Configure PHY interrupt function,Supported chip is:RTL8211FS
 *
 * @param   none.
 *
 * @return  none.
 */
void PHY_InterruptInit(void)
{
    uint16_t RegValue;

    ETH_WritePHYRegister(gPHYAddress, 0x1F, 0x0a42 );
    RegValue = ETH_ReadPHYRegister(gPHYAddress, 0x12);
    /* enable Link Status Change Interrupt and
     * Auto-Negotiation Completed Interrupt*/
    RegValue |= (1<<4)|(1<<3);
    ETH_WritePHYRegister(gPHYAddress, 0x12, RegValue );
    /* Clear the Interrupt status */
    ETH_WritePHYRegister( gPHYAddress, 0x1F, 0x0a43 );
    ETH_ReadPHYRegister( gPHYAddress, 0x1D);
}
#endif

/*********************************************************************
 * @fn      ETH_PHYLink
 *
 * @brief   Configure MAC parameters after the PHY Link is successful.
 *
 * @param   none.
 *
 * @return  none.
 */
void ETH_PHYLink( void )
{
    u32 phy_stat;

    ETH_WritePHYRegister( gPHYAddress, 0x1F, 0x0a43 );
    /*In some cases the status is not updated in time,
     * so read this register twice to get the correct status value.*/
    ETH_ReadPHYRegister( gPHYAddress, 0x1A);
    phy_stat = ETH_ReadPHYRegister( gPHYAddress, 0x1A);

#if !LINK_STAT_ACQUISITION_METHOD
    LastPhyStat = phy_stat & 0x04;
#endif
    WCHNET_PhyStatus( phy_stat );

    if( phy_stat & 0x04 )
    {
        /* Configure the polarity and delay of TXC */
        RGMII_TXC_Delay(0, 4);
        if( phy_stat & 0x08 )
        {
            ETH->MACCR |= ETH_Mode_FullDuplex;
        }
        else
        {
            ETH->MACCR &= ~ETH_Mode_FullDuplex;
        }
        if( (phy_stat & 0x30) == 0x00 )
        {
            ETH->MACCR &= ~(ETH_Speed_100M|ETH_Speed_1000M);
        }
        else if( (phy_stat & 0x30) == 0x10 )
        {
            ETH->MACCR &= ~(ETH_Speed_100M|ETH_Speed_1000M);
            ETH->MACCR |= ETH_Speed_100M;
        }
        else if( (phy_stat & 0x30) == 0x20 )
        {
            ETH->MACCR &= ~(ETH_Speed_100M|ETH_Speed_1000M);
            ETH->MACCR |= ETH_Speed_1000M;
            /* Configure the polarity and delay of TXC */
            RGMII_TXC_Delay(1, 4); 
        }
        ETH_Start( );
    }
    phy_stat = ETH_ReadPHYRegister( gPHYAddress, 0x1D);   /* Clear the Interrupt status */
}

/*********************************************************************
 * @fn      ETH_SetClock
 *
 * @brief   Set the Ethernet related clock
 *
 * @param   none.
 *
 * @return  none.
 */
void ETH_SetClock(void)
{
    RCC->CTLR |= 1<<26;
    while((RCC->CTLR & (1<<27)) == 0);
}

/*********************************************************************
 * @fn      ETH_RegInit
 *
 * @brief   ETH register initialization.
 *
 * @param   ETH_InitStruct:initialization struct.
 *          PHYAddress:PHY address.
 *
 * @return  Initialization status.
 */
uint32_t ETH_RegInit( ETH_InitTypeDef* ETH_InitStruct, uint16_t PHYAddress )
{
    uint16_t tmpreg = 0;
    /* Set the SMI interface clock, set as the main frequency divided by 42  */
    ETH->MACMIIAR = (uint32_t)ETH_MACMIIAR_CR_Div42;

    /*------------------------ MAC register configuration  -------------------------------------------*/
    ETH->MACCR = (uint32_t)(ETH_InitStruct->ETH_Watchdog |
                  ETH_InitStruct->ETH_Jabber |
                  ETH_InitStruct->ETH_InterFrameGap |
                  ETH_InitStruct->ETH_ChecksumOffload |
                  ETH_InitStruct->ETH_AutomaticPadCRCStrip |
                  ETH_InitStruct->ETH_LoopbackMode);

    ETH->MACFFR = (uint32_t)(ETH_InitStruct->ETH_ReceiveAll |
                          ETH_InitStruct->ETH_SourceAddrFilter |
                          ETH_InitStruct->ETH_PassControlFrames |
                          ETH_InitStruct->ETH_BroadcastFramesReception |
                          ETH_InitStruct->ETH_DestinationAddrFilter |
                          ETH_InitStruct->ETH_PromiscuousMode |
                          ETH_InitStruct->ETH_MulticastFramesFilter |
                          ETH_InitStruct->ETH_UnicastFramesFilter);

    ETH->MACHTHR = (uint32_t)ETH_InitStruct->ETH_HashTableHigh;
    ETH->MACHTLR = (uint32_t)ETH_InitStruct->ETH_HashTableLow;

    ETH->MACFCR = (uint32_t)((ETH_InitStruct->ETH_PauseTime << 16) |
                     ETH_InitStruct->ETH_UnicastPauseFrameDetect |
                     ETH_InitStruct->ETH_ReceiveFlowControl |
                     ETH_InitStruct->ETH_TransmitFlowControl);

    ETH->MACVLANTR = (uint32_t)(ETH_InitStruct->ETH_VLANTagComparison |
                               ETH_InitStruct->ETH_VLANTagIdentifier);

    ETH->DMAOMR = (uint32_t)(ETH_InitStruct->ETH_DropTCPIPChecksumErrorFrame |
                    ETH_InitStruct->ETH_TransmitStoreForward |
                    ETH_InitStruct->ETH_ForwardErrorFrames |
                    ETH_InitStruct->ETH_ForwardUndersizedGoodFrames);

    /* Reset the physical layer */
    tmpreg = ETH_ReadPHYRegister(PHYAddress, PHY_BCR);
    tmpreg |= PHY_Reset;
    ETH_WritePHYRegister(PHYAddress, PHY_BCR, tmpreg);
    return ETH_SUCCESS;
}

/*********************************************************************
 * @fn      ETH_Configuration
 *
 * @brief   Ethernet configure.
 *
 * @return  none
 */
void ETH_Configuration( uint8_t *macAddr )
{
    ETH_InitTypeDef ETH_InitStructure;
    uint16_t timeout = 10000;

    gPHYAddress = PHY_ADDRESS;
    
    /* Set the Ethernet related clock */
    ETH_SetClock();

    /* Enable Ethernet MAC clock */
    RCC->HBPCENR |= 1<<14;

    //Enable RGMII ON
    RCC->CFGR0 |= 1<<21;

    //Select 125M Clk Source
    RCC->CFGR2 |= 2<<30;

    /* Enable RGMII GPIO */
    ETH_RGMIIPinInit();

    /* Software reset */
    ETH_SoftwareReset();

    /* Wait for software reset */
    do{
        Delay_Us(10);
        if( !--timeout )  break;
    }while(ETH->DMABMR & ETH_DMABMR_SR);

    /* ETHERNET Configuration */
    /*------------------------   MAC   -----------------------------------*/
    ETH_InitStructure.ETH_Watchdog = ETH_Watchdog_Enable;
    ETH_InitStructure.ETH_Jabber = ETH_Jabber_Enable;
    ETH_InitStructure.ETH_InterFrameGap = ETH_InterFrameGap_96Bit;
#if HARDWARE_CHECKSUM_CONFIG
    ETH_InitStructure.ETH_ChecksumOffload = ETH_ChecksumOffload_Enable;
#else
    ETH_InitStructure.ETH_ChecksumOffload = ETH_ChecksumOffload_Disable;
#endif
    ETH_InitStructure.ETH_AutomaticPadCRCStrip = ETH_AutomaticPadCRCStrip_Disable;
    ETH_InitStructure.ETH_LoopbackMode = ETH_LoopbackMode_Disable;

    /* Filter function configuration */
    ETH_InitStructure.ETH_ReceiveAll = ETH_ReceiveAll_Enable;
    ETH_InitStructure.ETH_PromiscuousMode = ETH_PromiscuousMode_Enable;
    ETH_InitStructure.ETH_BroadcastFramesReception = ETH_BroadcastFramesReception_Enable;
    ETH_InitStructure.ETH_MulticastFramesFilter = ETH_MulticastFramesFilter_Perfect;
    ETH_InitStructure.ETH_UnicastFramesFilter = ETH_UnicastFramesFilter_Perfect;
    ETH_InitStructure.ETH_PassControlFrames = ETH_PassControlFrames_BlockAll;
    ETH_InitStructure.ETH_DestinationAddrFilter = ETH_DestinationAddrFilter_Normal;
    ETH_InitStructure.ETH_SourceAddrFilter = ETH_SourceAddrFilter_Disable;

    ETH_InitStructure.ETH_HashTableHigh = 0x0;
    ETH_InitStructure.ETH_HashTableLow = 0x0;

    /* VLan function configuration */
    ETH_InitStructure.ETH_VLANTagComparison = ETH_VLANTagComparison_16Bit;
    ETH_InitStructure.ETH_VLANTagIdentifier = 0x0;

    /* Flow Control function configuration */
    ETH_InitStructure.ETH_PauseTime = 0x0;
    ETH_InitStructure.ETH_UnicastPauseFrameDetect = ETH_UnicastPauseFrameDetect_Disable;
    ETH_InitStructure.ETH_ReceiveFlowControl = ETH_ReceiveFlowControl_Disable;
    ETH_InitStructure.ETH_TransmitFlowControl = ETH_TransmitFlowControl_Disable;

    /*------------------------   DMA   -----------------------------------*/
    /* When we use the Checksum offload feature, we need to enable the Store and Forward mode:
    the store and forward guarantee that a whole frame is stored in the FIFO, so the MAC can insert/verify the checksum,
    if the checksum is OK the DMA can handle the frame otherwise the frame is dropped */
    ETH_InitStructure.ETH_DropTCPIPChecksumErrorFrame = ETH_DropTCPIPChecksumErrorFrame_Enable;
    ETH_InitStructure.ETH_TransmitStoreForward = ETH_TransmitStoreForward_Enable;
    ETH_InitStructure.ETH_ForwardErrorFrames = ETH_ForwardErrorFrames_Enable;
    ETH_InitStructure.ETH_ForwardUndersizedGoodFrames = ETH_ForwardUndersizedGoodFrames_Enable;
    /* Configure Ethernet */
    ETH_RegInit( &ETH_InitStructure, gPHYAddress );

    /* Configure MAC address */
    ETH->MACA0HR = (uint32_t)((macAddr[5]<<8) | macAddr[4]);
    ETH->MACA0LR = (uint32_t)(macAddr[0] | (macAddr[1]<<8) | (macAddr[2]<<16) | (macAddr[3]<<24));

    /* Mask the interrupt that Tx good frame count counter reaches half the maximum value */
    ETH->MMCTIMR = ETH_MMCTIMR_TGFM;
    /* Mask the interrupt that Rx good unicast frames counter reaches half the maximum value */
    /* Mask the interrupt that Rx crc error counter reaches half the maximum value */
    ETH->MMCRIMR = ETH_MMCRIMR_RGUFM | ETH_MMCRIMR_RFCEM;

    ETH_DMAITConfig(ETH_DMA_IT_NIS |\
                ETH_DMA_IT_R |\
                ETH_DMA_IT_T |\
                ETH_DMA_IT_AIS |\
                ETH_DMA_IT_RBU,\
                ENABLE);

#if LINK_STAT_ACQUISITION_METHOD
    /* Configure the PHY interrupt function, the supported chip is: RTL8211FS */
    PHY_InterruptInit( );
    /* Configure EXTI Line7. */
    EXTI_Line_Init( );
#else
    ETH_WritePHYRegister( PHY_ADDRESS, 0x1F, 0x0a43 );
    /*In some cases the status is not updated in time,
     * so read this register twice to get the correct status value.*/
    ETH_ReadPHYRegister( PHY_ADDRESS, 0x1A);
    LastPhyStat = ETH_ReadPHYRegister( PHY_ADDRESS, 0x1A) & 0x04;
#endif
}

/*********************************************************************
 * @fn      ETH_TxPktChainMode
 *
 * @brief   Ethernet sends data frames in chain mode.
 *
 * @param   len     Send data length
 *          pBuff   send buffer pointer
 *
 * @return  Send status.
 */
uint32_t ETH_TxPktChainMode(uint16_t len, uint32_t *pBuff )
{
    /* Check if the descriptor is owned by the ETHERNET DMA (when set) or CPU (when reset) */
    if((DMATxDescToSet->Status & ETH_DMATxDesc_OWN) != (u32)RESET)
    {
        /* Return ERROR: OWN bit set */
        return ETH_ERROR;
    }
    /* Setting the Frame Length: bits[12:0] */
    DMATxDescToSet->ControlBufferSize = (len & ETH_DMATxDesc_TBS1);
    DMATxDescToSet->Buffer1Addr = (uint32_t)pBuff;

    /* Setting the last segment and first segment bits (in this case a frame is transmitted in one descriptor) */
#if HARDWARE_CHECKSUM_CONFIG
    DMATxDescToSet->Status |= ETH_DMATxDesc_LS | ETH_DMATxDesc_FS | ETH_DMATxDesc_CIC_TCPUDPICMP_Full;
#else
    DMATxDescToSet->Status |= ETH_DMATxDesc_LS | ETH_DMATxDesc_FS;
#endif

    /* Set Own bit of the Tx descriptor Status: gives the buffer back to ETHERNET DMA */
    DMATxDescToSet->Status |= ETH_DMATxDesc_OWN;

    /* Clear TBUS ETHERNET DMA flag */
    ETH->DMASR = ETH_DMASR_TBUS;
    /* Resume DMA transmission*/
    ETH->DMATPDR = 0;

    /* Update the ETHERNET DMA global Tx descriptor with next Tx descriptor */
    /* Chained Mode */
    /* Selects the next DMA Tx descriptor list for next buffer to send */
    DMATxDescToSet = (ETH_DMADESCTypeDef*) (DMATxDescToSet->Buffer2NextDescAddr);
    /* Return SUCCESS */
    return ETH_SUCCESS;
}

/*********************************************************************
 * @fn      WCHNET_ETHIsr
 *
 * @brief   Ethernet Interrupt Service Routine
 *
 * @return  none
 */
void WCHNET_ETHIsr(void)
{
    uint32_t intStat;

    intStat = ETH->DMASR;

    if (intStat & ETH_DMA_FLAG_AIS)
    {
        if (intStat & ETH_DMA_FLAG_RBU)
        {
            ETH_DMAClearITPendingBit(ETH_DMA_FLAG_RBU);
        }
        ETH_DMAClearITPendingBit(ETH_DMA_FLAG_AIS);
    }

    if( intStat & ETH_DMA_FLAG_NIS )
    {
        if( intStat & ETH_DMA_FLAG_R )
        {
            /*If you don't use the Ethernet library,
             * you can do some data processing operations here*/
            ETH_DMAClearITPendingBit(ETH_DMA_FLAG_R);
        }
        if( intStat & ETH_DMA_FLAG_T )
        {
            ETH_DMAClearITPendingBit(ETH_DMA_FLAG_T);
        }
        ETH_DMAClearITPendingBit(ETH_DMA_FLAG_NIS);
    }
}

/*********************************************************************
 * @fn      ETH_Init
 *
 * @brief   Ethernet initialization.
 *
 * @return  none
 */
void ETH_Init( uint8_t *macAddr )
{
    ETH_Configuration( macAddr );
    ETH_DMATxDescChainInit(DMATxDscrTab, MACTxBuf, ETH_TXBUFNB);
    ETH_DMARxDescChainInit(DMARxDscrTab, MACRxBuf, ETH_RXBUFNB);
    pDMARxSet = DMARxDscrTab;
    pDMATxSet = DMATxDscrTab;
    NVIC_EnableIRQ(ETH_IRQn);
    NVIC_SetPriority(ETH_IRQn, 0);
}

/*********************************************************************
 * @fn      ETH_LibInit
 *
 * @brief   Ethernet library initialization program
 *
 * @return  command status
 */
uint8_t ETH_LibInit( uint8_t *ip, uint8_t *gwip, uint8_t *mask, uint8_t *macaddr )
{
    uint8_t s;
    struct _WCH_CFG  cfg;

    memset(&cfg,0,sizeof(cfg));
    cfg.TxBufSize = ETH_TX_BUF_SZE;
    cfg.TCPMss   = WCHNET_TCP_MSS;
    cfg.HeapSize = WCHNET_MEM_HEAP_SIZE;
    cfg.ARPTableNum = WCHNET_NUM_ARP_TABLE;
    cfg.MiscConfig0 = WCHNET_MISC_CONFIG0;
    cfg.MiscConfig1 = WCHNET_MISC_CONFIG1;
    cfg.net_send = ETH_TxPktChainMode;
    cfg.CheckValid = WCHNET_CFG_VALID;
    s = WCHNET_ConfigLIB(&cfg);
    if( s ){
       return (s);
    }
    s = WCHNET_Init(ip,gwip,mask,macaddr);
    ETH_Init( macaddr );
    return (s);
}

/******************************** endfile @ eth_driver ******************************/
