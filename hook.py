def jal(imm):
    l = [('jal', 'x1', imm)]
    return l


def jalr(rs):
    l = [('jalr', 'x0', rs, '0')]
    return l

def li(rs, imm):
    print(imm)
    l = [('li', (rs, imm))]
    return l