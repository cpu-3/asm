import ctypes
import re
import struct

INST_LEN = 32

reg_d = {
    'zero': 0,
    'ra': 1,
    'sp': 2,
    'gp': 3,
    'tp': 4,
    't0': 5,
    't1': 6,
    't2': 7,
    's0': 8,
    'fp': 8,
    's1': 9,
    'a0': 10,
    'a1': 11,
    'a2': 12,
    'a3': 13,
    'a4': 14,
    'a5': 15,
    'a6': 16,
    'a7': 17,
    's2': 18,
    's3': 19,
    's4': 20,
    's5': 21,
    's6': 22,
    's7': 23,
    's8': 24,
    's9': 25,
    's10': 26,
    's11': 27,
    't3': 28,
    't4': 29,
    't5': 30,
    't6': 31,
}

def check_and_trans_reg(name):
    m = re.match(r'x\d{1,2}', name)
    if m is not None:
        if int(name[1:]) < 32:
            return int(name[1:])

    if name in reg_d:
        return reg_d[name]

    print('{} のようなレジスタは存在しません'.format(name))
    raise Exception('No Such Register')

def check_and_trans_imm(imm, size):
    try:
        val = int(imm)
    except Exception as e:
        print('{} を整数に変換できませんでした'.format(imm))
        raise e
    val = ctypes.c_ulong(val).value & 0xfffff

    l = len(bin(val)) - 2
    '''
    # このチェックは、妥当に行うのが難しそうなので一度外している
    if l > size:
        print('{} は即値として大きすぎます。{} bit以下でなければなりません'.format(imm, size))
        raise Exception('Too big')
    '''

    return val

def check_alignment(imm, size):
    if imm % size != 0:
        print('{} は {}-byte アラインメントされていません', imm, size)
        raise Exception('Alignment Error')

def pack(tuples):
    # check
    cnt = 0
    val = 0
    for (code, length) in tuples:
        val <<= length
        val += code
        cnt += length

    if cnt != INST_LEN:
        print('アセンブラがバグっていて、命令の長さが32bitになっていません')
        raise Exception('Bit Length Error')
    print(bin(val))
    return struct.pack('<L', val)

def lui(rd, imm):
    rd = check_and_trans_reg(rd)
    imm = check_and_trans_imm(imm, 20)
    return pack([
        (0b0110111, 7),
        (rd, 5),
        (v, 20)
        ])

def auipc(rd, imm):
    rd = check_and_trans_reg(rd)
    imm = check_and_trans_imm(imm, 20)
    v = imm & 0xfffff
    return pack([
        (0b0010111, 7),
        (rd, 5),
        (v, 20)
        ])

def bit_reorder(v, l):
    ret = 0
    for (i, x) in enumerate(l):
        mask = 1 << i
        ret <<= 1
        ret |= mask & v
    return ret

def jal(rd, imm):
    rd = check_and_trans_reg(rd)
    imm = check_and_trans_imm(imm, 21)
    check_alignment(imm, 2)
    v = imm & 0xfffff
    return pack([
        (0b1101111, 7),
        (rd, 5),
        (bit_reorder(v, [20, *range(1, 11), 11, *range(12, 20)]), 20)
    ])

def jalr(rd, rs, imm):
    rd = check_and_trans_reg(rd)
    rs = check_and_trans_reg(rs)
    imm = check_and_trans_imm(imm, 12)
    v = imm & 0xfffff
    return pack([
        (0b1101111, 7),
        (rd, 5),
        (0, 3),
        (rs, 5),
        (v, 12),
    ])

def branch(imm, funct3, rs1, rs2):
    imm = check_and_trans_imm(imm, 13)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    val = ((imm >> 1) & 0b1111) | ((imm >> 11) & 1)
    val2 = ((imm >> 5) & 0b111111) | ((imm >> 12) & 1)
    return pack([
        (0b1100011, 7),
        (val, 5),
        (funct3, 3),
        (rs1, 5),
        (rs2, 5),
        (val2, 7)
    ])

def beq(imm, rs1, rs2):
    return branch(imm, 0b000, rs1, rs2)

def bne(imm, rs1, rs2):
    return branch(imm, 0b001, rs1, rs2)

def blt(imm, rs1, rs2):
    return branch(imm, 0b100, rs1, rs2)

def bge(imm, rs1, rs2):
    return branch(imm, 0b101, rs1, rs2)

def bltu(imm, rs1, rs2):
    return branch(imm, 0b110, rs1, rs2)

def bgeu(imm, rs1, rs2):
    return branch(imm, 0b111, rs1, rs2)

def alui(rd, funct3, rs1, imm):
    imm = check_and_trans_imm(imm, 12)
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    return pack([
        (0b0010011, 7),
        (rd, 5),
        (funct3, 3),
        (rs1, 5),
        (imm, 12)
    ])

def shift(rd, funct3, rs1, imm1, imm2):
    return alui(rd, funct3, rs1, imm1 | (imm2 << 5))

def addi(rd, rs1, imm):
    return alui(rd, 0b000, rs1, imm)

def slti(rd, rs1, imm):
    return alui(rd, 0b010, rs1, imm)

def sltiu(rd, rs1, imm):
    return alui(rd, 0b011, rs1, imm)

def xori(rd, rs1, imm):
    return alui(rd, 0b100, rs1, imm)

def ori(rd, rs1, imm):
    return alui(rd, 0b100, rs1, imm)

def andi(rd, rs1, imm):
    return alui(rd, 0b111, rs1, imm)

def slli(rd, rs1, imm):
    return shift(rd, 0b001, rs1, imm, 0)

def srli(rd, rs1, imm):
    return shift(rd, 0b101, rs1, imm, 0)

def srai(rd, rs1, imm):
    return shift(rd, 0b101, rs1, imm, 0b0100000)

def load(rd, funct3, rs1, imm):
    imm = check_and_trans_imm(imm, 12)
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    return pack([
        (0b0000011, 7),
        (rd, 5),
        (funct3, 3),
        (rs1, 5),
        (imm, 12)
    ])

def lb(rd, rs1, imm):
    return load(rd, 0b000, rs1, imm)

def lh(rd, rs1, imm):
    return load(rd, 0b001, rs1, imm)

def lw(rd, rs1, imm):
    return load(rd, 0b010, rs1, imm)

def lbu(rd, rs1, imm):
    return load(rd, 0b100, rs1, imm)

def lhu(rd, rs1, imm):
    return load(rd, 0b101, rs1, imm)

def store(funct3, rs1, rs2, imm):
    imm = check_and_trans_imm(imm, 12)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    val = (imm & 0b11111)
    val2 = (imm >> 5)
    return pack([
        (0b0000011, 7),
        (val, 5),
        (funct3, 3),
        (rs1, 5),
        (rs2, 5),
        (val2, 7),
    ])

def sb(rs1, rs2, imm):
    return store(0b000, rs1, rs2, imm)

def sh(rs1, rs2, imm):
    return store(0b001, rs1, rs2, imm)

def sw(rs1, rs2, imm):
    return store(0b010, rs1, rs2, imm)

def pack_alu(opcode, rd, funct3, rs1, rs2, funct7):
    l = [
        (opcode, 7),
        (rd, 5),
        (funct3, 3),
        (rs1, 5),
        (rs2, 5),
        (funct7, 7)
        ]
    return pack(l)

def add(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b000, rs1, rs2, 0b0000000)

def sub(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b000, rs1, rs2, 0b0100000)

def sll(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b001, rs1, rs2, 0b0000000)

def slt(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b010, rs1, rs2, 0b0000000)

def sltu(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b011, rs1, rs2, 0b0000000)

def xor(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b100, rs1, rs2, 0b0000000)

def srl(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b101, rs1, rs2, 0b0000000)

def sra(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b101, rs1, rs2, 0b0100000)

def or_(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b110, rs1, rs2, 0b0000000)

def and_(rd, rs1, rs2):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    return pack_alu(0b0110011, rd, 0b111, rs1, rs2, 0b0000000)
