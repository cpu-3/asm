	.text
	.globl _min_caml_start
	.align 2
fib.1:
	add	sp, sp, -32
	sw	ra, 24(sp)
	sw	s0, 16(sp)
	add	s0, sp, 32
	li	s10, 1
	bgt	a0, s10, ble_else.15
	j	fib.1_end
ble_else.15:
	sub	a1, a0, 1
	sw	a0, 0(sp)
	add	a0, a1, 0
	sw	s10, 4(sp)
	call	fib.1
	lw	s10, 4(sp)
	lw	a1, 0(sp)
	sub	a1, a1, 2
	sw	a0, 4(sp)
	add	a0, a1, 0
	sw	s10, 12(sp)
	call	fib.1
	lw	s10, 12(sp)
	lw	a1, 4(sp)
	add	a0, a1, a0
	j	fib.1_end
fib.1_end:
	lw	ra, 24(sp)
	lw	s0, 16(sp)
	add	sp, sp, 32
	ret

_min_caml_start:
    addi    a0, zero, 7
    call    fib.1
    call min_caml_print_int
