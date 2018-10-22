import utils


def li(rd, imm):
    imm = utils.check_and_trans_imm(imm, 32)
    ui = str(imm >> 12)
    li = str(imm & ((1 << 12) - 1))
    l = [
        ('lui', [rd, ui]),
        ('addi', [rd, rd, li])
    ]
    return l


def mv(rd, rs):
    l = [('addi', [rd, rs, '0'])]
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

def jump(dst):
    l = [('jal', ('x0', dst))]
    return l

def jumpl(dst):
    l = [('jal', ('ra', dst))]
    return l


def call(imm):
    imm = utils.check_and_trans_imm(imm, 32)
    ui = str((imm >> 12) + ((imm >> 11) & 1))
    li = str(imm & ((1 << 12) - 1))
    l = [
        ('auipc', ('x1', ui)),
        ('jalr', ('x1', 'x1', li)),
    ]
    return l


def jr(rs):
    l = [('jalr', ('x0', rs, '0'))]
    return l


def jrl(rs):
    l = [('jalr', ('x1', rs, '0'))]
    return l


def ret():
    l = [('jalr', ('x0', 'x1', '0'))]
    return l


def tail(imm):
    imm = utils.check_and_trans_imm(imm, 32)
    ui = str((imm >> 12) + ((imm >> 11) & 1))
    li = str(imm & (1 << 12 - 1))
    l = [
        ('auipc', ('x6', ui)),
        ('jalr', ('x0', 'x6', li)),
    ]
    return l


def nop():
    l = [('addi', ('x0', 'x0', '0'))]
    return l

# 嘘が入っている可能性
def subi(rd, rs1, imm):
    if imm[0] == '-':
        imm = imm[1:]
    else:
        imm = '-' + imm
    l = [('addi', (rd, rs1, imm))]
    return l

def fmv(rd, rs):
    return [('fsgnj.s', (rd, rs, rs))]
