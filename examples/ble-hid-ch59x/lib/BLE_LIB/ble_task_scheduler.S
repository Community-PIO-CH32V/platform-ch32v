.global Ecall_M_Mode_Handler
.global Ecall_U_Mode_Handler
.global LLE_IRQHandler

.extern g_LLE_IRQLibHandlerLocation

.section	.highcode,"ax",@progbits
.align 2
.func
Ecall_M_Mode_Handler:
Ecall_U_Mode_Handler:

	addi a1, x0, 0x20
	csrs 0x804, a1

	lw a1, 0 * 4( sp )
	csrw mepc, a1

	lw x1, 1 * 4( sp )
	lw x4, 2 * 4( sp )
	lw x5, 3 * 4( sp )
	lw x6, 4 * 4( sp )
	lw x7, 5 * 4( sp )
	lw x8, 6 * 4( sp )
	lw x9, 7 * 4( sp )
	lw x10, 8 * 4( sp )
	lw x11, 9 * 4( sp )
	lw x12, 10 * 4( sp )
	lw x13, 11 * 4( sp )
	lw x14, 12 * 4( sp )
	lw x15, 13 * 4( sp )
	lw x16, 14 * 4( sp )
	lw x17, 15 * 4( sp )
	lw x18, 16 * 4( sp )
	lw x19, 17 * 4( sp )
	lw x20, 18 * 4( sp )
	lw x21, 19 * 4( sp )
	lw x22, 20 * 4( sp )
	lw x23, 21 * 4( sp )
	lw x24, 22 * 4( sp )
	lw x25, 23 * 4( sp )
	lw x26, 24 * 4( sp )
	lw x27, 25 * 4( sp )
	lw x28, 26 * 4( sp )
	lw x29, 27 * 4( sp )
	lw x30, 28 * 4( sp )
	lw x31, 29 * 4( sp )

	addi sp, sp, 32*4

	mret
	.endfunc

.section	.highcode.LLE_IRQHandler,"ax",@progbits
.align 2
.func
LLE_IRQHandler:
	addi sp, sp, -32*4

	sw x1, 1 * 4( sp )
	sw x4, 2 * 4( sp )
	sw x5, 3 * 4( sp )
	sw x6, 4 * 4( sp )
	sw x7, 5 * 4( sp )
	sw x8, 6 * 4( sp )
	sw x9, 7 * 4( sp )
	sw x10, 8 * 4( sp )
	sw x11, 9 * 4( sp )
	sw x12, 10 * 4( sp )
	sw x13, 11 * 4( sp )
	sw x14, 12 * 4( sp )
	sw x15, 13 * 4( sp )
	sw x16, 14 * 4( sp )
	sw x17, 15 * 4( sp )
	sw x18, 16 * 4( sp )
	sw x19, 17 * 4( sp )
	sw x20, 18 * 4( sp )
	sw x21, 19 * 4( sp )
	sw x22, 20 * 4( sp )
	sw x23, 21 * 4( sp )
	sw x24, 22 * 4( sp )
	sw x25, 23 * 4( sp )
	sw x26, 24 * 4( sp )
	sw x27, 25 * 4( sp )
	sw x28, 26 * 4( sp )
	sw x29, 27 * 4( sp )
	sw x30, 28 * 4( sp )
	sw x31, 29 * 4( sp )

	la a1, g_LLE_IRQLibHandlerLocation
	lw a0, 0(a1)
	jalr x1, 0(a0)

	lw x1, 1 * 4( sp )
	lw x4, 2 * 4( sp )
	lw x5, 3 * 4( sp )
	lw x6, 4 * 4( sp )
	lw x7, 5 * 4( sp )
	lw x8, 6 * 4( sp )
	lw x9, 7 * 4( sp )
	lw x10, 8 * 4( sp )
	lw x11, 9 * 4( sp )
	lw x12, 10 * 4( sp )
	lw x13, 11 * 4( sp )
	lw x14, 12 * 4( sp )
	lw x15, 13 * 4( sp )
	lw x16, 14 * 4( sp )
	lw x17, 15 * 4( sp )
	lw x18, 16 * 4( sp )
	lw x19, 17 * 4( sp )
	lw x20, 18 * 4( sp )
	lw x21, 19 * 4( sp )
	lw x22, 20 * 4( sp )
	lw x23, 21 * 4( sp )
	lw x24, 22 * 4( sp )
	lw x25, 23 * 4( sp )
	lw x26, 24 * 4( sp )
	lw x27, 25 * 4( sp )
	lw x28, 26 * 4( sp )
	lw x29, 27 * 4( sp )
	lw x30, 28 * 4( sp )
	lw x31, 29 * 4( sp )

	addi sp, sp, 32*4

	mret
	.endfunc
