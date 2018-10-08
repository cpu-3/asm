import utils


def li(rd, imm):
    imm = utils.check_and_trans_imm(imm, 32)
    ui = str(imm >> 12)
    li = str(imm & (1 << 12 - 1))
    l = [
        ('lui', [rd, ui]),
        ('addi', [rd, rd, li])
    ]
    return l


def mv(rd, rs):
    l = [('mv', [rd, rs])]
    return l


def bgt(rs, rt, imm):
    l = [('blt', (rt, rs, imm))]
    return l


def ble(rs, rt, imm):
    l = [('bge', (rt, rs, imm))]
    return l


def bgtu(rs, rt, imm):
    l = [('bltu', (rt, rs, imm))]
    return l


def bleu(rs, rt, imm):
    l = [('bgeu', (rt, rs, imm))]
    return l