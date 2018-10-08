def jal(imm):
    l = [('jal', 'x1', imm)]
    return l


def jalr(rs):
    l = [('jalr', 'x0', rs, '0')]
    return l