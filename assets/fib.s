fib:
    addi    sp,sp,-48
    sw    ra,40(sp)
    sw    s0,32(sp)
    sw    s1,24(sp)
    addi    s0,sp,48
    sw    a0,-36(s0)
    lw    a4,-36(s0)
    li    a5,1
    bgtu    a4,a5,.L2
    lw    a5,-36(s0)
    j    .L3
.L2:
    lw    a5,-36(s0)
    addi    a5,a5,-1
    mv    a0,a5
    call fib
    mv    s1,a0
    lw    a5,-36(s0)
    addi a5,a5,-2
    mv    a0,a5
    call fib
    mv    a5,a0
    add a5,s1,a5
.L3:
    mv    a0,a5
    lw    ra,40(sp)
    lw    s0,32(sp)
    lw    s1,24(sp)
    addi    sp,sp,48
    jr    ra
_min_caml_start:
    addi    a0, zero, 6
    call    fib
