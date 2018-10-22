from utils import check_alignment
from utils import check_and_trans_imm
from utils import check_and_trans_reg
from utils import pack


default_rm = 0b000

def lui(rd, imm):
    rd = check_and_trans_reg(rd)
    imm = check_and_trans_imm(imm, 20)
    return pack([
        (0b0110111, 7),
        (rd, 5),
        (imm, 20)
        ])

def auipc(rd, imm):
    rd = check_and_trans_reg(rd)
    v = check_and_trans_imm(imm, 20)
    return pack([
        (0b0010111, 7),
        (rd, 5),
        (v, 20)
        ])

def bit_reorder(v, l):
    ret = 0
    for x in l:
        tmp = (v >> x) & 1
        ret <<= 1
        ret |= tmp
    return ret

def jal(rd, imm):
    rd = check_and_trans_reg(rd)
    imm = check_and_trans_imm(imm, 21)
    check_alignment(imm, 2)
    return pack([
        (0b1101111, 7),
        (rd, 5),
        (bit_reorder(imm, [20, *range(10, 0, -1), 11, *range(19, 11, -1)]), 20)
    ])

def jalr(rd, rs, imm):
    rd = check_and_trans_reg(rd)
    rs = check_and_trans_reg(rs)
    v = check_and_trans_imm(imm, 12)
    return pack([
        (0b1100111, 7),
        (rd, 5),
        (0, 3),
        (rs, 5),
        (v, 12),
    ])

def branch(imm, funct3, rs1, rs2):
    imm = check_and_trans_imm(imm, 13)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    val = (((imm >> 1) & 0b1111) << 1) | ((imm >> 11) & 1)
    val2 = ((imm >> 5) & 0b111111) | (((imm >> 12) & 1) << 6)
    return pack([
        (0b1100011, 7),
        (val, 5),
        (funct3, 3),
        (rs1, 5),
        (rs2, 5),
        (val2, 7)
    ])

def beq(rs1, rs2, imm):
    return branch(imm, 0b000, rs1, rs2)

def bne(rs1, rs2, imm):
    return branch(imm, 0b001, rs1, rs2)

def blt(rs1, rs2, imm):
    return branch(imm, 0b100, rs1, rs2)

def bge(rs1, rs2, imm):
    return branch(imm, 0b101, rs1, rs2)

def bltu(rs1, rs2, imm):
    return branch(imm, 0b110, rs1, rs2)

def bgeu(rs1, rs2, imm):
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
    imm1 = check_and_trans_imm(imm1, 7)
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    return pack([
        (0b0010011, 7),
        (rd, 5),
        (funct3, 3),
        (rs1, 5),
        (imm1, 5),
        (imm2, 7)
    ])

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
        (0b0100011, 7),
        (val, 5),
        (funct3, 3),
        (rs2, 5),
        (rs1, 5),
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


def flw(rd, rs1, imm):
    imm = check_and_trans_imm(imm, 12)
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    return pack([
        (0b0000111, 7),
        (rd, 5),
        (0b010, 3),
        (rs1, 5),
        (imm, 12)
    ])


def fsw(rs1, rs2, imm):
    imm = check_and_trans_imm(imm, 12)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    val = (imm & 0b11111)
    val2 = (imm >> 5)
    return pack([
        (0b0100111, 7),
        (val, 5),
        (0b010, 3),
        (rs2, 5),
        (rs1, 5),
        (val2, 7),
    ])


def falu(rd, rm, rs1, rs2, funct7):
    rd = check_and_trans_reg(rd)
    rs1 = check_and_trans_reg(rs1)
    rs2 = check_and_trans_reg(rs2)
    l = [
        (0b1010011, 7),
        (rd, 5),
        (rm, 3),
        (rs1, 5),
        (rs2, 5),
        (funct7, 7)
        ]
    return pack(l)


def fadd(rd, rs1, rs2):
    return falu(rd, default_rm, rs1, rs2, 0b0000000)


def fsub(rd, rs1, rs2):
    return falu(rd, default_rm, rs1, rs2, 0b0000100)


def fmul(rd, rs1, rs2):
    return falu(rd, default_rm, rs1, rs2, 0b0001000)


def fdiv(rd, rs1, rs2):
    return falu(rd, default_rm, rs1, rs2, 0b0001100)


def fsqrt(rd, rs):
    # 'x0' -> 00000
    return falu(rd, default_rm, rs, 'x0', 0b0101100)


def feq(rd, rs1, rs2):
    return falu(rd, 0b010, rs1, rs2, 0b1010000)


def flt(rd, rs1, rs2):
    return falu(rd, 0b001, rs1, rs2, 0b1010000)


def fle(rd, rs1, rs2):
    return falu(rd, 0b000, rs1, rs2, 0b1010000)


def fsgnj(rd, rs1, rs2):
    return falu(rd, 0b000, rs1, rs2, 0b0010000)


def fsgnjn(rd, rs1, rs2):
    return falu(rd, 0b001, rs1, rs2, 0b0010000)


def fsgnjx(rd, rs1, rs2):
    return falu(rd, 0b010, rs1, rs2, 0b0010000)


def fcvt_w_s(rd, rs):
    return falu(rd, default_rm, rs, 'x0', 0b1100000)


def fcvt_s_w(rd, rs):
    return falu(rd, default_rm, rs, 'x0', 0b1101000)