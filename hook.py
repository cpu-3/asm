def jal(imm):
    l = [('jal', 'x1', imm)]
    return l


def jalr(rs):
    l = [('jalr', 'x0', rs, '0')]
    return l

def li(rs, imm):
    l = [('li', (rs, imm))]
    return l


def add(rd, rs, imm):
    l = [('addi', (rd, rs, imm))]
    return l


def sub(rd, rs, imm):
    l = [('subi', (rd, rs, imm))]
    return l
