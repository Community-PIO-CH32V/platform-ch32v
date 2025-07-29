.option norelax
.equ compressed_isa,1

.text
.global _start

.include "regs.inc"

_start:
li t0, RCC
li t1, IOPCEN
sw t1, RCC_APB2PCENR(t0)

li t0, GPIOC
li t2, 0xFFFFF00
and t1, t1, t2
ori t1, t1, 0x00000022
sw t1, CFGLR(t0)


#li t0, GPIOC
#li t1, (ResetValue & PINA_Clear) | PINA_Output_PP_2MHz | PINB_Output_PP_2MHz
#sw t1, CFGLR(t0)
#li t0, GPIOC
#li t1, (ResetValue & PINB_Clear) | PINB_Output_PP_2MHz
#sw t1, CFGLR(t0)

lw t1, OUTDR(t0)
xori t1, t1, 1<<PINA
xori t1, t1, 1<<PINB
sw t1, OUTDR(t0)


1:
lw t1, OUTDR(t0)
xori t1, t1, 0b10
sw t1, OUTDR(t0)

li t2, 1000000
2:
add t2, t2, -1
bnez t2, 2b

j 1b