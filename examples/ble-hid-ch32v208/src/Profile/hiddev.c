/********************************** (C) COPYRIGHT *******************************
 * File Name          : hiddev.c
 * Author             : WCH
 * Version            : V1.0
 * Date               : 2018/12/10
 * Description        : HID device task handler
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/*********************************************************************
 * INCLUDES
 */

#include "config.h"
#include "battservice.h"
#include "scanparamservice.h"
#include "devinfoservice.h"
#include "hidkbd.h"
#include "hiddev.h"

/*********************************************************************
 * MACROS
 */

// Battery measurement period in (625us)
#define DEFAULT_BATT_PERIOD               15000

// TRUE to run scan parameters refresh notify test
#define DEFAULT_SCAN_PARAM_NOTIFY_TEST    TRUE

// Advertising intervals (units of 625us, 160=100ms)
#define HID_INITIAL_ADV_INT_MIN           48
#define HID_INITIAL_ADV_INT_MAX           80
#define HID_HIGH_ADV_INT_MIN              32
#define HID_HIGH_ADV_INT_MAX              48
#define HID_LOW_ADV_INT_MIN               160
#define HID_LOW_ADV_INT_MAX               160

// Advertising timeouts in sec
#define HID_INITIAL_ADV_TIMEOUT           60
#define HID_HIGH_ADV_TIMEOUT              5
#define HID_LOW_ADV_TIMEOUT               0

// Heart Rate Task Events
#define START_DEVICE_EVT                  0x0001
#define BATT_PERIODIC_EVT                 0x0002

/*********************************************************************
 * CONSTANTS
 */

/*********************************************************************
 * TYPEDEFS
 */

/*********************************************************************
 * GLOBAL VARIABLES
 */

// Task ID
uint8_t hidDevTaskId;

/*********************************************************************
 * EXTERNAL VARIABLES
 */

/*********************************************************************
 * EXTERNAL FUNCTIONS
 */

/*********************************************************************
 * LOCAL VARIABLES
 */

// GAP State
static gapRole_States_t hidDevGapState = GAPROLE_INIT;

// TRUE if connection is secure
static uint8_t hidDevConnSecure = FALSE;

// GAP connection handle
static uint16_t gapConnHandle;

// Status of last pairing
static uint8_t pairingStatus = SUCCESS;

static hidRptMap_t *pHidDevRptTbl;

static uint8_t hidDevRptTblLen;

static hidDevCB_t *pHidDevCB;

static hidDevCfg_t *pHidDevCfg;

/*********************************************************************
 * LOCAL FUNCTIONS
 */

static void hidDev_ProcessTMOSMsg(tmos_event_hdr_t *pMsg);
static void hidDevProcessGattMsg(gattMsgEvent_t *pMsg);
static void hidDevProcessGAPMsg(gapRoleEvent_t *pEvent);
static void hidDevDisconnected(void);
static void hidDevGapStateCB(gapRole_States_t newState, gapRoleEvent_t *pEvent);
static void hidDevParamUpdateCB(uint16_t connHandle, uint16_t connInterval,
                                uint16_t connSlaveLatency, uint16_t connTimeout);
static void hidDevPairStateCB(uint16_t connHandle, uint8_t state, uint8_t status);
static void hidDevPasscodeCB(uint8_t *deviceAddr, uint16_t connectionHandle,
                             uint8_t uiInputs, uint8_t uiOutputs);
static void hidDevBattCB(uint8_t event);
static void hidDevScanParamCB(uint8_t event);
static void hidDevBattPeriodicTask(void);

static hidRptMap_t *hidDevRptByHandle(uint16_t handle);
static hidRptMap_t *hidDevRptById(uint8_t id, uint8_t type);
static hidRptMap_t *hidDevRptByCccdHandle(uint16_t handle);

static uint8_t hidDevSendReport(uint8_t id, uint8_t type, uint8_t len, uint8_t *pData);
static void    hidDevHighAdvertising(void);
static void    hidDevLowAdvertising(void);
static void    hidDevInitialAdvertising(void);
static uint8_t hidDevBondCount(void);
static uint8_t HidDev_sendNoti(uint16_t handle, uint8_t len, uint8_t *pData);
/*********************************************************************
 * PROFILE CALLBACKS
 */

// GAP Role Callbacks
static gapRolesCBs_t hidDev_PeripheralCBs = {
    hidDevGapStateCB, // Profile State Change Callbacks
    NULL,             // When a valid RSSI is read from controller
    hidDevParamUpdateCB
};

// Bond Manager Callbacks
static gapBondCBs_t hidDevBondCB = {
    hidDevPasscodeCB,
    hidDevPairStateCB
};

/*********************************************************************
 * PUBLIC FUNCTIONS
 */

/*********************************************************************
 * @fn      HidDev_Init
 *
 * @brief   Initialization function for the Hid Dev Task.
 *          This is called during initialization and should contain
 *          any application specific initialization (ie. hardware
 *          initialization/setup, table initialization, power up
 *          notificaiton ... ).
 *
 * @param   task_id - the ID assigned by TMOS.  This ID should be
 *                    used to send messages and set timers.
 *
 * @return  none
 */
void HidDev_Init()
{
    hidDevTaskId = TMOS_ProcessEventRegister(HidDev_ProcessEvent);

    // Setup the GAP Bond Manager
    {
        uint8_t syncWL = TRUE;

        // If a bond is created, the HID Device should write the address of the
        // HID Host in the HID Device controller's white list and set the HID
        // Device controller's advertising filter policy to 'process scan and
        // connection requests only from devices in the White List'.
        GAPBondMgr_SetParameter(GAPBOND_AUTO_SYNC_WL, sizeof(uint8_t), &syncWL);
    }

    // Set up services
    GGS_AddService(GATT_ALL_SERVICES);         // GAP
    GATTServApp_AddService(GATT_ALL_SERVICES); // GATT attributes
    DevInfo_AddService();
    Batt_AddService();
    ScanParam_AddService();

    // Register for Battery service callback
    Batt_Register(hidDevBattCB);

    // Register for Scan Parameters service callback
    ScanParam_Register(hidDevScanParamCB);

    // Setup a delayed profile startup
    tmos_set_event(hidDevTaskId, START_DEVICE_EVT);
}

/*********************************************************************
 * @fn      HidDev_ProcessEvent
 *
 * @brief   Hid Dev Task event processor.  This function
 *          is called to process all events for the task.  Events
 *          include timers, messages and any other user defined events.
 *
 * @param   task_id  - The TMOS assigned task ID.
 * @param   events - events to process.  This is a bit map and can
 *                   contain more than one event.
 *
 * @return  events not processed
 */
uint16_t HidDev_ProcessEvent(uint8_t task_id, uint16_t events)
{
    //VOID task_id; // TMOS required parameter that isn't used in this function

    if(events & SYS_EVENT_MSG)
    {
        uint8_t *pMsg;

        if((pMsg = tmos_msg_receive(hidDevTaskId)) != NULL)
        {
            hidDev_ProcessTMOSMsg((tmos_event_hdr_t *)pMsg);

            // Release the TMOS message
            tmos_msg_deallocate(pMsg);
        }

        // return unprocessed events
        return (events ^ SYS_EVENT_MSG);
    }

    if(events & START_DEVICE_EVT)
    {
        // Start the Device
        GAPRole_PeripheralStartDevice(hidDevTaskId, &hidDevBondCB, &hidDev_PeripheralCBs);

        return (events ^ START_DEVICE_EVT);
    }

    if(events & BATT_PERIODIC_EVT)
    {
        // Perform periodic battery task
        hidDevBattPeriodicTask();

        return (events ^ BATT_PERIODIC_EVT);
    }

    return 0;
}

/*********************************************************************
 * @fn      HidDev_Register
 *
 * @brief   Register a callback function with HID Dev.
 *
 * @param   pCfg - Parameter configuration.
 * @param   pfnServiceCB - Callback function.
 *
 * @return  None.
 */
void HidDev_Register(hidDevCfg_t *pCfg, hidDevCB_t *pCBs)
{
    pHidDevCB = pCBs;
    pHidDevCfg = pCfg;
}

/*********************************************************************
 * @fn      HidDev_RegisterReports
 *
 * @brief   Register the report table with HID Dev.
 *
 * @param   numReports - Length of report table.
 * @param   pRpt - Report table.
 *
 * @return  None.
 */
void HidDev_RegisterReports(uint8_t numReports, hidRptMap_t *pRpt)
{
    pHidDevRptTbl = pRpt;
    hidDevRptTblLen = numReports;
}

/*********************************************************************
 * @fn      HidDev_Report
 *
 * @brief   Send a HID report.
 *
 * @param   id - HID report ID.
 * @param   type - HID report type.
 * @param   len - Length of report.
 * @param   pData - Report data.
 *
 * @return  None.
 */
uint8_t HidDev_Report(uint8_t id, uint8_t type, uint8_t len, uint8_t *pData)
{
    // if connected
    if(hidDevGapState == GAPROLE_CONNECTED)
    {
        // if connection is secure
        if(hidDevConnSecure)
        {
            // send report
            return hidDevSendReport(id, type, len, pData);
        }
    }
    // else if not already advertising
    else if(hidDevGapState != GAPROLE_ADVERTISING)
    {
        // if bonded
        if(hidDevBondCount() > 0)
        {
            // start high duty cycle advertising
            hidDevHighAdvertising();
        }
        // else not bonded
        else
        {
            // start initial advertising
            hidDevInitialAdvertising();
        }
    }
    return bleNotReady;
}

/*********************************************************************
 * @fn      HidDev_Close
 *
 * @brief   Close the connection or stop advertising.
 *
 * @return  None.
 */
void HidDev_Close(void)
{
    uint8_t param;

    // if connected then disconnect
    if(hidDevGapState == GAPROLE_CONNECTED)
    {
        GAPRole_TerminateLink(gapConnHandle);
    }
    // else stop advertising
    else
    {
        param = FALSE;
        GAPRole_SetParameter(GAPROLE_ADVERT_ENABLED, sizeof(uint8_t), &param);
    }
}

/*********************************************************************
 * @fn      HidDev_SetParameter
 *
 * @brief   Set a HID Dev parameter.
 *
 * @param   param - Profile parameter ID
 * @param   len - length of data to right
 * @param   pValue - pointer to data to write.  This is dependent on
 *          the parameter ID and WILL be cast to the appropriate
 *          data type (example: data type of uint16_t will be cast to
 *          uint16_t pointer).
 *
 * @return  bStatus_t
 */
bStatus_t HidDev_SetParameter(uint8_t param, uint8_t len, void *pValue)
{
    bStatus_t ret = SUCCESS;

    switch(param)
    {
        case HIDDEV_ERASE_ALLBONDS:
            if(len == 0)
            {
                // Drop connection
                if(hidDevGapState == GAPROLE_CONNECTED)
                {
                    GAPRole_TerminateLink(gapConnHandle);
                }

                // Erase bonding info
                GAPBondMgr_SetParameter(GAPBOND_ERASE_ALLBONDS, 0, NULL);
            }
            else
            {
                ret = bleInvalidRange;
            }
            break;

        default:
            ret = INVALIDPARAMETER;
            break;
    }

    return (ret);
}

/*********************************************************************
 * @fn      HidDev_GetParameter
 *
 * @brief   Get a HID Dev parameter.
 *
 * @param   param - Profile parameter ID
 * @param   pValue - pointer to data to get.  This is dependent on
 *          the parameter ID and WILL be cast to the appropriate
 *          data type (example: data type of uint16_t will be cast to
 *          uint16_t pointer).
 *
 * @return  bStatus_t
 */
bStatus_t HidDev_GetParameter(uint8_t param, void *pValue)
{
    bStatus_t ret = SUCCESS;

    switch(param)
    {
        default:
            ret = INVALIDPARAMETER;
            break;
    }

    return (ret);
}

/*********************************************************************
 * @fn      HidDev_PasscodeRsp
 *
 * @brief   Respond to a passcode request.
 *
 * @param   status - SUCCESS if passcode is available, otherwise
 *                   see @ref SMP_PAIRING_FAILED_DEFINES.
 * @param   passcode - integer value containing the passcode.
 *
 * @return  none
 */
void HidDev_PasscodeRsp(uint8_t status, uint32_t passcode)
{
    // Send passcode response
    GAPBondMgr_PasscodeRsp(gapConnHandle, status, passcode);
}

/*********************************************************************
 * @fn          HidDev_ReadAttrCB
 *
 * @brief       HID Dev attribute read callback.
 *
 * @param       connHandle - connection message was received on
 * @param       pAttr - pointer to attribute
 * @param       pValue - pointer to data to be read
 * @param       pLen - length of data to be read
 * @param       offset - offset of the first octet to be read
 * @param       maxLen - maximum length of data to be read
 *
 * @return      Success or Failure
 */
bStatus_t HidDev_ReadAttrCB(uint16_t connHandle, gattAttribute_t *pAttr,
                            uint8_t *pValue, uint16_t *pLen, uint16_t offset, uint16_t maxLen, uint8_t method)
{
    bStatus_t    status = SUCCESS;
    hidRptMap_t *pRpt;

    uint16_t uuid = BUILD_UINT16(pAttr->type.uuid[0], pAttr->type.uuid[1]);

    // Only report map is long
    if(offset > 0 && uuid != REPORT_MAP_UUID)
    {
        return (ATT_ERR_ATTR_NOT_LONG);
    }

    if(uuid == REPORT_UUID ||
       uuid == BOOT_KEY_INPUT_UUID ||
       uuid == BOOT_KEY_OUTPUT_UUID ||
       uuid == BOOT_MOUSE_INPUT_UUID)
    {
        // find report ID in table
        if((pRpt = hidDevRptByHandle(pAttr->handle)) != NULL)
        {
            // execute report callback
            status = (*pHidDevCB->reportCB)(pRpt->id, pRpt->type, uuid,
                                            HID_DEV_OPER_READ, pLen, pValue);
        }
        else
        {
            *pLen = 0;
        }
    }
    else if(uuid == REPORT_MAP_UUID)
    {
        // verify offset
        if(offset >= hidReportMapLen)
        {
            status = ATT_ERR_INVALID_OFFSET;
        }
        else
        {
            // determine read length
            *pLen = MIN(maxLen, (hidReportMapLen - offset));

            // copy data
            tmos_memcpy(pValue, pAttr->pValue + offset, *pLen);
        }
    }
    else if(uuid == HID_INFORMATION_UUID)
    {
        *pLen = HID_INFORMATION_LEN;
        tmos_memcpy(pValue, pAttr->pValue, HID_INFORMATION_LEN);
    }
    else if(uuid == GATT_REPORT_REF_UUID)
    {
        *pLen = HID_REPORT_REF_LEN;
        tmos_memcpy(pValue, pAttr->pValue, HID_REPORT_REF_LEN);
    }
    else if(uuid == PROTOCOL_MODE_UUID)
    {
        *pLen = HID_PROTOCOL_MODE_LEN;
        pValue[0] = pAttr->pValue[0];
    }
    else if(uuid == GATT_EXT_REPORT_REF_UUID)
    {
        *pLen = HID_EXT_REPORT_REF_LEN;
        tmos_memcpy(pValue, pAttr->pValue, HID_EXT_REPORT_REF_LEN);
    }

    return (status);
}

/*********************************************************************
 * @fn      HidDev_WriteAttrCB
 *
 * @brief   HID Dev attribute read callback.
 *
 * @param   connHandle - connection message was received on
 * @param   pAttr - pointer to attribute
 * @param   pValue - pointer to data to be written
 * @param   len - length of data
 * @param   offset - offset of the first octet to be written
 *
 * @return  Success or Failure
 */
bStatus_t HidDev_WriteAttrCB(uint16_t connHandle, gattAttribute_t *pAttr,
                             uint8_t *pValue, uint16_t len, uint16_t offset, uint8_t method)
{
    uint16_t     uuid;
    bStatus_t    status = SUCCESS;
    hidRptMap_t *pRpt;

    // Make sure it's not a blob operation (no attributes in the profile are long)
    if(offset > 0)
    {
        return (ATT_ERR_ATTR_NOT_LONG);
    }

    uuid = BUILD_UINT16(pAttr->type.uuid[0], pAttr->type.uuid[1]);

    if(uuid == REPORT_UUID ||
       uuid == BOOT_KEY_OUTPUT_UUID)
    {
        // find report ID in table
        if((pRpt = hidDevRptByHandle(pAttr->handle)) != NULL)
        {
            // execute report callback
            status = (*pHidDevCB->reportCB)(pRpt->id, pRpt->type, uuid,
                                            HID_DEV_OPER_WRITE, &len, pValue);
        }
    }
    else if(uuid == HID_CTRL_PT_UUID)
    {
        // Validate length and value range
        if(len == 1)
        {
            if(pValue[0] == HID_CMD_SUSPEND || pValue[0] == HID_CMD_EXIT_SUSPEND)
            {
                // execute HID app event callback
                (*pHidDevCB->evtCB)((pValue[0] == HID_CMD_SUSPEND) ? HID_DEV_SUSPEND_EVT : HID_DEV_EXIT_SUSPEND_EVT);
            }
            else
            {
                status = ATT_ERR_INVALID_VALUE;
            }
        }
        else
        {
            status = ATT_ERR_INVALID_VALUE_SIZE;
        }
    }
    else if(uuid == GATT_CLIENT_CHAR_CFG_UUID)
    {
        status = GATTServApp_ProcessCCCWriteReq(connHandle, pAttr, pValue, len,
                                                offset, GATT_CLIENT_CFG_NOTIFY);
        if(status == SUCCESS)
        {
            uint16_t charCfg = BUILD_UINT16(pValue[0], pValue[1]);

            // find report ID in table
            if((pRpt = hidDevRptByCccdHandle(pAttr->handle)) != NULL)
            {
                // execute report callback
                (*pHidDevCB->reportCB)(pRpt->id, pRpt->type, uuid,
                                       (charCfg == GATT_CLIENT_CFG_NOTIFY) ? HID_DEV_OPER_ENABLE : HID_DEV_OPER_DISABLE,
                                       &len, pValue);
            }
        }
    }
    else if(uuid == PROTOCOL_MODE_UUID)
    {
        if(len == HID_PROTOCOL_MODE_LEN)
        {
            if(pValue[0] == HID_PROTOCOL_MODE_BOOT ||
               pValue[0] == HID_PROTOCOL_MODE_REPORT)
            {
                pAttr->pValue[0] = pValue[0];

                // execute HID app event callback
                (*pHidDevCB->evtCB)((pValue[0] == HID_PROTOCOL_MODE_BOOT) ? HID_DEV_SET_BOOT_EVT : HID_DEV_SET_REPORT_EVT);
            }
            else
            {
                status = ATT_ERR_INVALID_VALUE;
            }
        }
        else
        {
            status = ATT_ERR_INVALID_VALUE_SIZE;
        }
    }

    return (status);
}

/*********************************************************************
 * @fn      hidDev_ProcessTMOSMsg
 *
 * @brief   Process an incoming task message.
 *
 * @param   pMsg - message to process
 *
 * @return  none
 */
static void hidDev_ProcessTMOSMsg(tmos_event_hdr_t *pMsg)
{
    switch(pMsg->event)
    {
        case GATT_MSG_EVENT:
        {
            hidDevProcessGattMsg((gattMsgEvent_t *)pMsg);
            break;
        }

        case GAP_MSG_EVENT:
        {
            hidDevProcessGAPMsg((gapRoleEvent_t *)pMsg);
            break;
        }

        default:
            break;
    }
}

/*********************************************************************
 * @fn      hidDevProcessGattMsg
 *
 * @brief   Process GATT messages
 *
 * @return  none
 */
static void hidDevProcessGattMsg(gattMsgEvent_t *pMsg)
{
}

/*********************************************************************
 * @fn      hidDevProcessGAPMsg
 *
 * @brief   Process an incoming task message.
 *
 * @param   pMsg - message to process
 *
 * @return  none
 */
static void hidDevProcessGAPMsg(gapRoleEvent_t *pEvent)
{
    switch(pEvent->gap.opcode)
    {
        case GAP_SCAN_REQUEST_EVENT:
        {
            PRINT("recv scan Req addr ");
            for(int i = 0; i < B_ADDR_LEN; i++)
                PRINT("%02x ", pEvent->scanReqEvt.scannerAddr[i]);
            PRINT("\n");
            break;
        }

        case GAP_PHY_UPDATE_EVENT:
        {
            PRINT("Phy update Rx:%x Tx:%x ..\n", pEvent->linkPhyUpdate.connRxPHYS, pEvent->linkPhyUpdate.connTxPHYS);
            break;
        }
        default:
            break;
    }
}

/*********************************************************************
 * @fn          hidDevHandleConnStatusCB
 *
 * @brief       Reset client char config.
 *
 * @param       connHandle - connection handle
 * @param       changeType - type of change
 *
 * @return      none
 */
static void hidDevHandleConnStatusCB(uint16_t connHandle, uint8_t changeType)
{
    uint8_t          i;
    hidRptMap_t     *p = pHidDevRptTbl;
    uint16_t         retHandle;
    gattAttribute_t *pAttr;

    // Make sure this is not loopback connection
    if(connHandle != LOOPBACK_CONNHANDLE)
    {
        if((changeType == LINKDB_STATUS_UPDATE_REMOVED) ||
           ((changeType == LINKDB_STATUS_UPDATE_STATEFLAGS) &&
            (!linkDB_Up(connHandle))))
        {
            for(i = hidDevRptTblLen; i > 0; i--, p++)
            {
                if(p->cccdHandle != 0)
                {
                    if((pAttr = GATT_FindHandle(p->cccdHandle, &retHandle)) != NULL)
                    {
                        GATTServApp_InitCharCfg(connHandle, (gattCharCfg_t *)pAttr->pValue);
                    }
                }
            }
        }
    }
}

/*********************************************************************
 * @fn      hidDevDisconnected
 *
 * @brief   Handle disconnect.
 *
 * @return  none
 */
static void hidDevDisconnected(void)
{
    // Reset client characteristic configuration descriptors
    Batt_HandleConnStatusCB(gapConnHandle, LINKDB_STATUS_UPDATE_REMOVED);
    ScanParam_HandleConnStatusCB(gapConnHandle, LINKDB_STATUS_UPDATE_REMOVED);
    hidDevHandleConnStatusCB(gapConnHandle, LINKDB_STATUS_UPDATE_REMOVED);

    // Reset state variables
    hidDevConnSecure = FALSE;
    hidProtocolMode = HID_PROTOCOL_MODE_REPORT;

    // if bonded and normally connectable start advertising
    if((hidDevBondCount() > 0) &&
       (pHidDevCfg->hidFlags & HID_FLAGS_NORMALLY_CONNECTABLE))
    {
        hidDevLowAdvertising();
    }
}

/*********************************************************************
 * @fn      hidDevGapStateCB
 *
 * @brief   Notification from the profile of a state change.
 *
 * @param   newState - new state
 *
 * @return  none
 */
static void hidDevGapStateCB(gapRole_States_t newState, gapRoleEvent_t *pEvent)
{
    uint8_t param;
    // if connected
    if(newState == GAPROLE_CONNECTED)
    {
        gapEstLinkReqEvent_t *event = (gapEstLinkReqEvent_t *)pEvent;

        // get connection handle
        gapConnHandle = event->connectionHandle;

        // connection not secure yet
        hidDevConnSecure = FALSE;

        // don't start advertising when connection is closed
        param = FALSE;
        GAPRole_SetParameter(GAPROLE_ADVERT_ENABLED, sizeof(uint8_t), &param);
    }
    // if disconnected
    else if(hidDevGapState == GAPROLE_CONNECTED &&
            newState != GAPROLE_CONNECTED)
    {
        hidDevDisconnected();

        if(pairingStatus == SMP_PAIRING_FAILED_CONFIRM_VALUE)
        {
            // bonding failed due to mismatched confirm values
            hidDevInitialAdvertising();

            pairingStatus = SUCCESS;
        }
    }
    // if started
    else if(newState == GAPROLE_STARTED)
    {
        // nothing to do for now!
    }

    if(pHidDevCB && pHidDevCB->pfnStateChange)
    {
        // execute HID app state change callback
        (*pHidDevCB->pfnStateChange)(newState, pEvent);
    }

    hidDevGapState = newState;
}

/*********************************************************************
 * @fn      hidDevParamUpdateCB
 *
 * @brief   Parameter update complete callback
 *
 * @param   connHandle - connect handle
 *          connInterval - connect interval
 *          connSlaveLatency - connect slave latency
 *          connTimeout - connect timeout
 *
 * @return  none
 */
static void hidDevParamUpdateCB(uint16_t connHandle, uint16_t connInterval,
                                uint16_t connSlaveLatency, uint16_t connTimeout)
{
    PRINT("Update %d - Int 0x%x - Latency %d\n", connHandle, connInterval, connSlaveLatency);
}

/*********************************************************************
 * @fn      hidDevPairStateCB
 *
 * @brief   Pairing state callback.
 *
 * @return  none
 */
static void hidDevPairStateCB(uint16_t connHandle, uint8_t state, uint8_t status)
{
    if(state == GAPBOND_PAIRING_STATE_COMPLETE)
    {
        if(status == SUCCESS)
        {
            hidDevConnSecure = TRUE;
        }

        pairingStatus = status;
    }
    else if(state == GAPBOND_PAIRING_STATE_BONDED)
    {
        if(status == SUCCESS)
        {
            hidDevConnSecure = TRUE;

#if DEFAULT_SCAN_PARAM_NOTIFY_TEST == TRUE
            ScanParam_RefreshNotify(gapConnHandle);
#endif
        }
    }
    else if(state == GAPBOND_PAIRING_STATE_BOND_SAVED)
    {
    }
}

/*********************************************************************
 * @fn      hidDevPasscodeCB
 *
 * @brief   Passcode callback.
 *
 * @param   deviceAddr - address of device to pair with, and could be either public or random.
 * @param   connectionHandle - connection handle
 * @param   uiInputs - pairing User Interface Inputs - Ask user to input passcode
 * @param   uiOutputs - pairing User Interface Outputs - Display passcode
 *
 * @return  none
 */
static void hidDevPasscodeCB(uint8_t *deviceAddr, uint16_t connectionHandle,
                             uint8_t uiInputs, uint8_t uiOutputs)
{
    if(pHidDevCB && pHidDevCB->passcodeCB)
    {
        // execute HID app passcode callback
        (*pHidDevCB->passcodeCB)(deviceAddr, connectionHandle, uiInputs, uiOutputs);
    }
    else
    {
        uint32_t passkey;
        GAPBondMgr_GetParameter(GAPBOND_PERI_DEFAULT_PASSCODE, &passkey);

        // Send passcode response
        GAPBondMgr_PasscodeRsp(connectionHandle, SUCCESS, passkey);
    }
}

/*********************************************************************
 * @fn      hidDevBattCB
 *
 * @brief   Callback function for battery service.
 *
 * @param   event - service event
 *
 * @return  none
 */
static void hidDevBattCB(uint8_t event)
{
    if(event == BATT_LEVEL_NOTI_ENABLED)
    {
        tmos_start_task(hidDevTaskId, BATT_PERIODIC_EVT, DEFAULT_BATT_PERIOD);
    }
    else if(event == BATT_LEVEL_NOTI_DISABLED)
    {
        // stop periodic measurement
        tmos_stop_task(hidDevTaskId, BATT_PERIODIC_EVT);
    }
}

/*********************************************************************
 * @fn      hidDevScanParamCB
 *
 * @brief   Callback function for scan parameter service.
 *
 * @param   event - service event
 *
 * @return  none
 */
static void hidDevScanParamCB(uint8_t event)
{
}

/*********************************************************************
 * @fn      hidDevBattPeriodicTask
 *
 * @brief   Perform a periodic task for battery measurement.
 *
 * @param   none
 *
 * @return  none
 */
static void hidDevBattPeriodicTask(void)
{
    // perform battery level check
    Batt_MeasLevel();

    // Restart timer
    tmos_start_task(hidDevTaskId, BATT_PERIODIC_EVT, DEFAULT_BATT_PERIOD);
}

/*********************************************************************
 * @fn      hidDevRptByHandle
 *
 * @brief   Find the HID report structure for the given handle.
 *
 * @param   handle - ATT handle
 *
 * @return  Pointer to HID report structure
 */
static hidRptMap_t *hidDevRptByHandle(uint16_t handle)
{
    uint8_t      i;
    hidRptMap_t *p = pHidDevRptTbl;

    for(i = hidDevRptTblLen; i > 0; i--, p++)
    {
        if(p->handle == handle && p->mode == hidProtocolMode)
        {
            return p;
        }
    }

    return NULL;
}

/*********************************************************************
 * @fn      hidDevRptByCccdHandle
 *
 * @brief   Find the HID report structure for the given CCC handle.
 *
 * @param   handle - ATT handle
 *
 * @return  Pointer to HID report structure
 */
static hidRptMap_t *hidDevRptByCccdHandle(uint16_t handle)
{
    uint8_t      i;
    hidRptMap_t *p = pHidDevRptTbl;

    for(i = hidDevRptTblLen; i > 0; i--, p++)
    {
        if(p->cccdHandle == handle)
        {
            return p;
        }
    }

    return NULL;
}

/*********************************************************************
 * @fn      hidDevRptById
 *
 * @brief   Find the HID report structure for the Report ID and type.
 *
 * @param   id - HID report ID
 * @param   type - HID report type
 *
 * @return  Pointer to HID report structure
 */
static hidRptMap_t *hidDevRptById(uint8_t id, uint8_t type)
{
    uint8_t      i;
    hidRptMap_t *p = pHidDevRptTbl;

    for(i = hidDevRptTblLen; i > 0; i--, p++)
    {
        if(p->id == id && p->type == type && p->mode == hidProtocolMode)
        {
            return p;
        }
    }

    return NULL;
}

/*********************************************************************
 * @fn      hidDevSendReport
 *
 * @brief   Send a HID report.
 *
 * @param   id - HID report ID.
 * @param   type - HID report type.
 * @param   len - Length of report.
 * @param   pData - Report data.
 *
 * @return  None.
 */
static uint8_t hidDevSendReport(uint8_t id, uint8_t type, uint8_t len, uint8_t *pData)
{
    hidRptMap_t     *pRpt;
    gattAttribute_t *pAttr;
    uint16_t         retHandle;
    uint8_t          state = bleNoResources;

    // get att handle for report
    if((pRpt = hidDevRptById(id, type)) != NULL)
    {
        // if notifications are enabled
        if((pAttr = GATT_FindHandle(pRpt->cccdHandle, &retHandle)) != NULL)
        {
            uint16_t value;

            value = GATTServApp_ReadCharCfg(gapConnHandle, (gattCharCfg_t *)pAttr->pValue);
            if(value & GATT_CLIENT_CFG_NOTIFY)
            {
                // Send report notification
                state = HidDev_sendNoti(pRpt->handle, len, pData);
            }
        }
    }
    return state;
}

/*********************************************************************
 * @fn      hidDevSendNoti
 *
 * @brief   Send a HID notification.
 *
 * @param   handle - Attribute handle.
 * @param   len - Length of report.
 * @param   pData - Report data.
 *
 * @return  Success or failure.
 */
static uint8_t HidDev_sendNoti(uint16_t handle, uint8_t len, uint8_t *pData)
{
    uint8_t              status;
    attHandleValueNoti_t noti;

    noti.pValue = GATT_bm_alloc(gapConnHandle, ATT_HANDLE_VALUE_NOTI, len, NULL, 0);
    if(noti.pValue != NULL)
    {
        noti.handle = handle;
        noti.len = len;
        tmos_memcpy(noti.pValue, pData, len);

        // Send notification
        status = GATT_Notification(gapConnHandle, &noti, FALSE);
        if(status != SUCCESS)
        {
            GATT_bm_free((gattMsg_t *)&noti, ATT_HANDLE_VALUE_NOTI);
        }
    }
    else
    {
        status = bleMemAllocError;
    }

    return status;
}

/*********************************************************************
 * @fn      hidDevHighAdvertising
 *
 * @brief   Start advertising at a high duty cycle.

 * @param   None.
 *
 * @return  None.
 */
static void hidDevHighAdvertising(void)
{
    uint8_t param;

    GAP_SetParamValue(TGAP_DISC_ADV_INT_MIN, HID_HIGH_ADV_INT_MIN);
    GAP_SetParamValue(TGAP_DISC_ADV_INT_MAX, HID_HIGH_ADV_INT_MAX);
    GAP_SetParamValue(TGAP_LIM_ADV_TIMEOUT, HID_HIGH_ADV_TIMEOUT);

    param = TRUE;
    GAPRole_SetParameter(GAPROLE_ADVERT_ENABLED, sizeof(uint8_t), &param);
}

/*********************************************************************
 * @fn      hidDevLowAdvertising
 *
 * @brief   Start advertising at a low duty cycle.
 *
 * @param   None.
 *
 * @return  None.
 */
static void hidDevLowAdvertising(void)
{
    uint8_t param;

    GAP_SetParamValue(TGAP_DISC_ADV_INT_MIN, HID_LOW_ADV_INT_MIN);
    GAP_SetParamValue(TGAP_DISC_ADV_INT_MAX, HID_LOW_ADV_INT_MAX);
    GAP_SetParamValue(TGAP_LIM_ADV_TIMEOUT, HID_LOW_ADV_TIMEOUT);

    param = TRUE;
    GAPRole_SetParameter(GAPROLE_ADVERT_ENABLED, sizeof(uint8_t), &param);
}

/*********************************************************************
 * @fn      hidDevInitialAdvertising
 *
 * @brief   Start advertising for initial connection
 *
 * @return  None.
 */
static void hidDevInitialAdvertising(void)
{
    uint8_t param;

    GAP_SetParamValue(TGAP_DISC_ADV_INT_MIN, HID_INITIAL_ADV_INT_MIN);
    GAP_SetParamValue(TGAP_DISC_ADV_INT_MAX, HID_INITIAL_ADV_INT_MAX);
    GAP_SetParamValue(TGAP_LIM_ADV_TIMEOUT, HID_INITIAL_ADV_TIMEOUT);

    param = TRUE;
    GAPRole_SetParameter(GAPROLE_ADVERT_ENABLED, sizeof(uint8_t), &param);
}

/*********************************************************************
 * @fn      hidDevBondCount
 *
 * @brief   Gets the total number of bonded devices.
 *
 * @param   None.
 *
 * @return  number of bonded devices.
 */
static uint8_t hidDevBondCount(void)
{
    uint8_t bondCnt = 0;

    GAPBondMgr_GetParameter(GAPBOND_BOND_COUNT, &bondCnt);

    return (bondCnt);
}

/*********************************************************************
*********************************************************************/
