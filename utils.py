import ctypes
import struct
import re


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


def get_reg(name):
    if type(name) != str and type(name) != bytes:
        return None

    m = re.match(r'x\d{1,2}', name)
    if m is not None:
        if int(name[1:]) < 32:
            return int(name[1:])

    if name in reg_d:
        return reg_d[name]
    return None


def is_reservations(name):
    r = get_reg(name)
    if r is not None:
        return True
    return False


def is_number(name):
    m = re.match(r'-\d+', name)
    return m is not None


def is_special(name):
    return is_number(name) or is_reservations(name)

def int2uint(imm, bit_len=32):
    return ctypes.c_ulong(imm).value & (2 ** bit_len - 1)


def check_and_trans_reg(name):
    r = get_reg(name)
    if r is not None:
        return r
    print('{} のようなレジスタは存在しません'.format(name))
    raise Exception('No Such Register')


def check_and_trans_imm(imm, size):
    try:
        val = int(imm)
    except Exception as e:
        print('{} を整数に変換できませんでした'.format(imm))
        raise e

    val = int2uint(val, size)

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
