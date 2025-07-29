#ENTRY( InterruptVector )

MEMORY
{
   flash(rx)   : ORIGIN = 0x00000000, LENGTH = 16K
   ram(xrw) : ORIGIN = 0x20000000, LENGTH = 2K
}

SECTIONS
{
   .text : { KEEP(*(.text)) *(.text.*)  } > flash
   .bss  : { *(.bss*) } > ram
}
