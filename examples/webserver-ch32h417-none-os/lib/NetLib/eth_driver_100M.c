/********************************** (C) COPYRIGHT *******************************
* File Name          : eth_driver.c
* Author             : WCH
* Version            : V1.0.0
* Date               : 2024/05/05
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
volatile uint32_t LocalTime;
volatile uint8_t PhyWaitNegotiationSuc = 0;
ETH_DMADESCTypeDef *pDMARxSet;
ETH_DMADESCTypeDef *pDMATxSet;

uint8_t ESDCheckCnt = 0;
volatile uint8_t LinkSta = 0;  //0:Link down 1:Link up
uint8_t LinkVaildFlag = 0;  //0:invalid 1:valid
uint8_t LinkProcessingStep = 0;
uint32_t LinkProcessingTime = 0;
uint32_t TaskExecutionTime = 0;
void ETH_LinkDownCfg(uint16_t phy_bsr);

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

void WCHNET_QueryPhySta(void)
{
    if(PhyWaitNegotiationSuc)
    {
        ETH_PHYLink();
    }
}

/*********************************************************************
 * @fn      WCHNET_CheckPHYPN
 *
 * @brief   check PHY PN polarity
 *
 * @return  none.
 */
void WCHNET_CheckPHYPN(uint16_t time)
{
    u16 phy_stat;
    //check PHY PN
    if((LinkProcessingStep == 0)||(LocalTime >= LinkProcessingTime))
    {
        ETH_WritePHYRegister(gPHYAddress, PHY_PAG_SEL, PHY_REG_PAGE0 );
        phy_stat = ETH_ReadPHYRegister( gPHYAddress, PHY_STATUS);
        if(phy_stat & (1<<4))
        {
            if(LinkProcessingStep == 0)
            {
                LinkProcessingStep = 1;
                LinkProcessingTime = LocalTime + time;
            }
            else {
                LinkProcessingStep = 0;
                LinkProcessingTime = 0;
                phy_stat = ETH_ReadPHYRegister( gPHYAddress, PHY_ANER);
                if((time == 200) || ((phy_stat & 1) == 0))
                {
                    phy_stat = ETH_ReadPHYRegister( gPHYAddress, PHY_CONTROL1);
                    phy_stat |= 1;
                    ETH_WritePHYRegister(gPHYAddress, PHY_CONTROL1, phy_stat );
                }
            }
        }
        else {
            LinkProcessingStep = 0;
            LinkProcessingTime = 0;
        }
    }
}

/*********************************************************************
 * @fn      WCHNET_CheckLinkVaild
 *
 * @brief   check whether Link is valid
 *
 * @return  none.
 */
void WCHNET_CheckLinkVaild(void)
{
    uint16_t phy_stat, phy_bcr;

    if(LinkVaildFlag == 0)
    {
        phy_bcr = ETH_ReadPHYRegister( PHY_ADDRESS, PHY_BCR);
        if((phy_bcr & (1<<13)) == 0)   //Do nothing if Link mode is 10M.
        {
            LinkVaildFlag = 1;
            LinkProcessingTime = 0;
            return;
        }
        ETH_WritePHYRegister(gPHYAddress, PHY_PAG_SEL, 99 );
        phy_stat = ETH_ReadPHYRegister( gPHYAddress, 0x1b);
        if((phy_stat & (1<<2)) == 0)
        {
            LinkProcessingTime++;
            if(LinkProcessingTime == 5)
            {
                LinkProcessingTime = 0;
                phy_stat = ETH_ReadPHYRegister(gPHYAddress, PHY_BCR);
                ETH_WritePHYRegister(gPHYAddress, PHY_BCR, PHY_Reset );
                Delay_Us(100);
                ETH_WritePHYRegister(gPHYAddress, PHY_BCR, phy_stat );
                ETH_LinkDownCfg(0);
            }
        }
        else {
            LinkProcessingTime = 0;
        }
    }
}

/*********************************************************************
 * @fn      WCHNET_ESDExceptionHandling
 *
 * @brief   When the PHY is in an abnormal state during ESD testing, reset it.
 *
 * @return  none.
 */
void WCHNET_ESDExceptionHandling(void)
{
    uint16_t phy_val;
    ETH_WritePHYRegister( PHY_ADDRESS, PHY_PAG_SEL, 0x00 );
    phy_val= ETH_ReadPHYRegister( PHY_ADDRESS, 0x14 );
    if(phy_val)
    {
        ESDCheckCnt++;
        if(ESDCheckCnt == 6)
        {
            ESDCheckCnt = 0;
            phy_val = ETH_ReadPHYRegister(PHY_ADDRESS, PHY_BCR);
            ETH_WritePHYRegister(PHY_ADDRESS, PHY_BCR, PHY_Reset );
            Delay_Us(100);
            ETH_WritePHYRegister(PHY_ADDRESS, PHY_BCR, phy_val );
            ETH_LinkDownCfg(0);
        }
    }
    else {
            ESDCheckCnt = 0;
    }
}

/*********************************************************************
 * @fn      WCHNET_LinkProcessing
 *
 * @brief   process Link stage task
 *
 * @return  none.
 */
void WCHNET_LinkProcessing(void)
{
    u16 phy_bcr;

    if(LocalTime >= TaskExecutionTime)
    {
        TaskExecutionTime = LocalTime + 20;         //execution cycle:20ms
        if(LinkSta == 0)                            //Link down
        {
            phy_bcr = ETH_ReadPHYRegister( PHY_ADDRESS, PHY_BCR);
            if(phy_bcr & PHY_AutoNegotiation)       //auto-negotiation is enabled
            {
                WCHNET_CheckPHYPN(300);             //check PHY PN
            }
            else {                                  //auto-negotiation is disabled
                if((phy_bcr & (1<<13)) == 0)        // 10M
                {
                    WCHNET_CheckPHYPN(200);         //check PHY PN
                }
            }
        }
        else {                                      //Link up
            WCHNET_CheckLinkVaild();                //check whether Link is valid
            WCHNET_ESDExceptionHandling();          //ESD Exception Handle
        }
    }
}

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
    WCHNET_QueryPhySta();                   /* Query external PHY status */
    WCHNET_LinkProcessing();                /* process Link stage task */
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
 * @fn      ETH_LinkUpCfg
 *
 * @brief   When the PHY is connected, configure the relevant functions.
 *
 * @param   phy_bsr PHY Link status.
 *
 * @return  none.
 */
void ETH_LinkUpCfg(uint16_t phy_bsr)
{
    uint16_t phy_stat;

    PHY_PARA_CFG();
    LinkSta = 1;
    LinkProcessingStep = 0;
    LinkProcessingTime = 0;
    PhyWaitNegotiationSuc = 0;
    ETH_Start( );

    WCHNET_PhyStatus( phy_bsr );
    ETH_WritePHYRegister(gPHYAddress, PHY_PAG_SEL, PHY_REG_PAGE0 );
    phy_stat = ETH_ReadPHYRegister( PHY_ADDRESS, PHY_STATUS );
    if(phy_stat & PHY_SPEED_100M_MODE)
    {
        if(phy_stat & PHY_FULL_DUPLEX_MODE)
        {
            ETH->MACCR |= ETH_Mode_FullDuplex;
        }
        else
        {
            ETH->MACCR &= ~ETH_Mode_FullDuplex;
        } 
        ETH->MACCR &= ~(3<<14); 
        ETH->MACCR |= ETH_Speed_100M;
    }
    else {
        if(phy_stat & PHY_FULL_DUPLEX_MODE)
        {
            ETH->MACCR |= ETH_Mode_FullDuplex;
        }
        else
        {
            ETH->MACCR &= ~ETH_Mode_FullDuplex;
        } 
        ETH->MACCR &= ~(3<<14); 
        ETH->MACCR |= ETH_Speed_10M;
    }
}

/*********************************************************************
 * @fn      ETH_LinkDownCfg
 *
 * @brief   When the PHY is disconnected, configure the relevant functions.
 *
 * @param   phy_bsr PHY Link status.
 *
 * @return  none.
 */
void ETH_LinkDownCfg(uint16_t phy_bsr)
{
    WCHNET_PhyStatus( phy_bsr );
    LinkSta = 0;
    LinkVaildFlag = 0;
    LinkProcessingTime = 0;
}

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
    u32 phy_bsr, phy_anlpar, phy_bcr;

    phy_bsr = ETH_ReadPHYRegister( PHY_ADDRESS, PHY_BSR );
    phy_anlpar = ETH_ReadPHYRegister( PHY_ADDRESS, PHY_ANLPAR);
    phy_bcr = ETH_ReadPHYRegister( gPHYAddress, PHY_BCR);

    if(phy_bsr & PHY_Linked_Status)   //LinkUp
    {
        if(phy_bcr & PHY_AutoNegotiation)
        {
            if(phy_anlpar == 0)
            {
                ETH_LinkUpCfg(phy_bsr);
            }
            else {
                if(phy_bsr & PHY_AutoNego_Complete)
                {
                    ETH_LinkUpCfg(phy_bsr);
                }
                else{
                    PhyWaitNegotiationSuc = 1;
                }
            }
        }
        else {
            ETH_LinkUpCfg(phy_bsr);
        }
    }
    else {                              //LinkDown
        /*Link down*/
        ETH_LinkDownCfg(phy_bsr);
    }
    ETH_WritePHYRegister(gPHYAddress, PHY_PAG_SEL, PHY_REG_PAGE0 );
    ETH_ReadPHYRegister( gPHYAddress, PHY_INTERRUPT_IND);   /* Clear the Interrupt status */
}

/*********************************************************************
 * @fn      PHY_InterruptInit
 *
 * @brief   Configure PHY interrupt function
 *
 * @param   none.
 *
 * @return  none.
 */
void PHY_InterruptInit(void)
{
    uint16_t RegValue;

    ETH_WritePHYRegister(gPHYAddress, PHY_PAG_SEL, PHY_REG_PAGE7 );
    /* Configure interrupt function */
    RegValue = ETH_ReadPHYRegister(gPHYAddress, PHY_INTERRUPT_MASK);
    RegValue |= 0x01 << 13;
    ETH_WritePHYRegister(gPHYAddress, PHY_INTERRUPT_MASK, RegValue );
    /* Clear the Interrupt status */
    ETH_WritePHYRegister(gPHYAddress, PHY_PAG_SEL, PHY_REG_PAGE0 );
    ETH_ReadPHYRegister( gPHYAddress, PHY_INTERRUPT_IND);
}

/*********************************************************************
 * @fn      PHY_LEDCfg
 *
 * @brief   Configure PHY LED function
 *
 * @param   none.
 *
 * @return  none.
 */
void PHY_LEDCfg(void)
{
    uint16_t RegValue;
	GPIO_InitTypeDef  GPIO_InitStructure;

    RCC_HB2PeriphClockCmd(RCC_HB2Periph_AFIO | RCC_HB2Periph_GPIOF, ENABLE);
    GPIO_PinAFConfig(GPIOF, GPIO_PinSource0, GPIO_AF10);    //Link
    GPIO_PinAFConfig(GPIOF, GPIO_PinSource2, GPIO_AF10);    //ACT

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_Very_High;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(GPIOF, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_Very_High;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(GPIOF, &GPIO_InitStructure);

    ETH_WritePHYRegister(gPHYAddress, PHY_PAG_SEL, PHY_REG_PAGE7 );
    //turn on LED--PHY
    RegValue = ETH_ReadPHYRegister(gPHYAddress, PHY_INTERRUPT_MASK);
    RegValue |= 1<<9;
    ETH_WritePHYRegister(gPHYAddress, PHY_INTERRUPT_MASK, RegValue );
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

    /* Disable PHY Powerdown */
    ETH->MACPHYCR &= ~(1<<30);

    /* Disable PHY Rstn */
    ETH->MACPHYCR |= 1<<31;

    /* Reset ETHERNET on AHB Bus */
    // ETH_DeInit();

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
    ETH_InitStructure.ETH_ChecksumOffload = ETH_ChecksumOffload_Disable;
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

    PHY_InterruptInit();

    ETH_DMAITConfig(ETH_DMA_IT_NIS |\
                ETH_DMA_IT_R |\
                ETH_DMA_IT_T |\
                ETH_DMA_IT_AIS |\
                ETH_DMA_IT_RBU |\
                ETH_DMA_IT_PHYSR,\
                ENABLE);
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

    // /* Set Own bit of the Tx descriptor Status: gives the buffer back to ETHERNET DMA */
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
        if( intStat & ETH_DMA_FLAG_PHYSR)
        {
            ETH_PHYLink();
            ETH_DMAClearITPendingBit(ETH_DMA_FLAG_PHYSR);
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
    PHY_LEDCfg();
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
