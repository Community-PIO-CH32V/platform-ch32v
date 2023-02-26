#ifndef __CH32V_IT_H
#define __CH32V_IT_H

#include "debug.h"


#define GET_INT_SP()   asm("csrrw sp,mscratch,sp")
#define FREE_INT_SP()  asm("csrrw sp,mscratch,sp")

#endif /* __CH32V_IT_H */