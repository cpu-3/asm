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

    l = bin(val) - 2
    if l > size:
        print('{} は即値として大きすぎます。{} bit以下でなければなりません'.format(imm, size))

    return val

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
    pass

def auipc(rd, imm):
    rd = check_and_trans_reg(rd)
    imm = check_and_trans_imm(imm, 20)
    pass

def jal(rd, imm):
    rd = check_and_trans_reg(rd)
    imm = check_and_trans_imm(imm, 20)
    pass

def jalr(rd, rs, imm):
    rd = check_and_trans_reg(rd)
    rs = check_and_trans_reg(rs)
    imm = check_and_trans_imm(imm, 12)
    pass

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
