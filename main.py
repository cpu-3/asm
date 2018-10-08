'''
 ** instant ** assembler implementation

 fileを二回りするような実装。前提として一命令が4byteで構成されている。
 一般にアセンブラは、.s -> .oの変換を行い、.oファイルたちをリンカがリンクする
 というのが一般的だが、ファイルが複数になることはなさそうなことと、まぁそれほど
 大規模なプログラムはコンパイルしないだろうということ、命令の長さが決まっていることや
 展開される場所が決まっていることから、まぁ、こういう構成でええやろみたいな判断

 1. タグを前から探していき、その位置を記録する
 2. 前から順に、アセンブリを機械語に変換する。このとき、jmp命令の即値は
   適切に書き換える

'''

import argparse
import re
import unittest

import asmgen
import extension
import utils


read_bytes = 0
tags = {}  # map[tag]int

debug = True

tag_re = r'((?P<tag_name>[_|\w|.]*):)'
r = r'^\s*' + tag_re + r'.*$'
tag_pat = re.compile(r)


def error_line(line):
    print('エラーの発生した行: {}'.format(line))


def parse_tag_line(s):
    m = tag_pat.match(s)
    if m is not None:
        if utils.is_reservations(s):
            print('{} は予約語です'.format(s))
        tags[m.group('tag_name')] = read_bytes


def _solve_tag(name):
    if name not in tags:
        print('{} は見つかりませんでした。'.format(name))
        raise Exception('Tag is not found')

    addr = tags[name]
    return addr

    
def solve_tag_relative(name):
    return read_bytes - _solve_tag(name)


def solve_tag_absolute(name):
    return _solve_tag(addr)


def check_args(name, args, length):
    if (len(args) == length):
        return

    print('{} should have {} args. But got {}'.format(name, length, len(args)))
    print('  -> {} {}', name, ','.join(args))
    raise(Exception('Syntax Error'))


displacement_res = r'^(?P<offset>(-?\d+)?)\((?P<reg>.+)\)$'
displacement_re = re.compile(displacement_res)


def match_displacement(s):
    m = displacement_re.match(s)
    if m is None:
        return None

    offset = m.group('offset')
    reg = m.group('reg')

    if offset == '':
        return (reg, '0')
    else:
        return (reg, offset)


class TestDisplacementRegex(unittest.TestCase):
    ''' Does displacement regex work correctly? '''

    def test_displacement_match(self):
        r = displacement_re
        self.assertIsNotNone(r.match('10(sp)'))
        self.assertIsNotNone(r.match('-10(sp)'))
        self.assertIsNotNone(r.match('(sp)'))
        self.assertIsNone(r.match('hoge'))
        self.assertIsNone(r.match('100'))

    def test_displacement_values(self):
        m = displacement_re.match('-18(sp)')
        self.assertIsNotNone(m)
        offset = m.group('offset')
        reg = m.group('reg')
        self.assertEqual(offset, '-18')
        self.assertEqual(reg, 'sp')

        m = displacement_re.match('(t1)')
        self.assertIsNotNone(m)
        offset = m.group('offset')
        reg = m.group('reg')
        self.assertEqual(offset, '')
        self.assertEqual(reg, 't1')

    def test_match_dislacement_func(self):
        self.assertEqual(match_displacement('-18(sp)'), ('sp', '-18'))
        self.assertEqual(match_displacement('(t10)'), ('t10', '0'))
        self.assertIsNone(match_displacement('t10'))


def handle_args(args):
    ret = []
    for arg in args:
        r = match_displacement(arg)
        if r is not None:
            # 再帰的にパターンが存在するかを（一応）確認する
            l = handle_args(r)
            ret += l
        else:
            ret.append(arg)
    return ret


def handle_extension(name, args):
    if name == 'li':
        check_args(name, args, 2)
        return extension.li(args[0], args[1])
    elif name == 'mv':
        check_args(name, args, 2)
        return extension.mv(args[0], args[1])
    elif name == 'bgt':
        check_args(name, args, 3)
        return extension.bgt(args[0], args[1], args[2])
    elif name == 'ble':
        check_args(name, args, 3)
        return extension.ble(args[0], args[1], args[2])
    elif name == 'bgtu':
        check_args(name, args, 3)
        return extension.bgtu(args[0], args[1], args[2])
    elif name == 'bleu':
        check_args(name, args, 3)
        return extension.bleu(args[0], args[1], args[2])
    else:
        return None


def asm(name, args):
    args = handle_args(args)
    if name == 'lui':
        check_args(name, args, 2)
        return asmgen.lui(args[0], args[1])
    elif name == 'auipc':
        check_args(name, args, 2)
        return asmgen.auipc(args[0], args[1])
    elif name == 'add':
        check_args(name, args, 3)
        return asmgen.add(args[0], args[1], args[2])
    elif name == 'sub':
        check_args(name, args, 3)
        return asmgen.sub(args[0], args[1], args[2])
    elif name == 'sll':
        check_args(name, args, 3)
        return asmgen.sll(args[0], args[1], args[2])
    elif name == 'slt':
        check_args(name, args, 3)
        return asmgen.slt(args[0], args[1], args[2])
    elif name == 'sltu':
        check_args(name, args, 3)
        return asmgen.sltu(args[0], args[1], args[2])
    elif name == 'xor':
        check_args(name, args, 3)
        return asmgen.xor(args[0], args[1], args[2])
    elif name == 'srl':
        check_args(name, args, 3)
        return asmgen.srl(args[0], args[1], args[2])
    elif name == 'sra':
        check_args(name, args, 3)
        return asmgen.sra(args[0], args[1], args[2])
    elif name == 'or':
        check_args(name, args, 3)
        return asmgen.or_(args[0], args[1], args[2])
    elif name == 'and':
        check_args(name, args, 3)
        return asmgen.and_(args[0], args[1], args[2])
    elif name == 'lui':
        check_args(name, args, 2)
        return asmgen.lui(args[0], args[1])
    elif name == 'auipc':
        check_args(name, args, 2)
        return asmgen.auipc(args[0], args[1])
    elif name == 'jal':
        check_args(name, args, 2)
        return asmgen.jal(args[0], args[1])
    elif name == 'jalr':
        check_args(name, args, 3)
        return asmgen.jalr(args[0], args[1], args[2])
    elif name == 'beq':
        check_args(name, args, 3)
        return asmgen.beq(args[0], args[1], args[2])
    elif name == 'bne':
        check_args(name, args, 3)
        return asmgen.bne(args[0], args[1], args[2])
    elif name == 'blt':
        check_args(name, args, 3)
        return asmgen.blt(args[0], args[1], args[2])
    elif name == 'bge':
        check_args(name, args, 3)
        return asmgen.bge(args[0], args[1], args[2])
    elif name == 'bltu':
        check_args(name, args, 3)
        return asmgen.bltu(args[0], args[1], args[2])
    elif name == 'bgeu':
        check_args(name, args, 3)
        return asmgen.bgeu(args[0], args[1], args[2])
    elif name == 'addi':
        check_args(name, args, 3)
        return asmgen.addi(args[0], args[1], args[2])
    elif name == 'slti':
        check_args(name, args, 3)
        return asmgen.slti(args[0], args[1], args[2])
    elif name == 'sltiu':
        check_args(name, args, 3)
        return asmgen.sltiu(args[0], args[1], args[2])
    elif name == 'sltiu':
        check_args(name, args, 3)
        return asmgen.sltiu(args[0], args[1], args[2])
    elif name == 'xori':
        check_args(name, args, 3)
        return asmgen.xori(args[0], args[1], args[2])
    elif name == 'ori':
        check_args(name, args, 3)
        return asmgen.ori(args[0], args[1], args[2])
    elif name == 'andi':
        check_args(name, args, 3)
        return asmgen.andi(args[0], args[1], args[2])
    elif name == 'slli':
        check_args(name, args, 3)
        return asmgen.slli(args[0], args[1], args[2])
    elif name == 'srai':
        check_args(name, args, 3)
        return asmgen.srai(args[0], args[1], args[2])
    elif name == 'lb':
        check_args(name, args, 3)
        return asmgen.lb(args[0], args[1], args[2])
    elif name == 'lh':
        check_args(name, args, 3)
        return asmgen.lh(args[0], args[1], args[2])
    elif name == 'lw':
        check_args(name, args, 3)
        return asmgen.lw(args[0], args[1], args[2])
    elif name == 'lbu':
        check_args(name, args, 3)
        return asmgen.lbu(args[0], args[1], args[2])
    elif name == 'lhu':
        check_args(name, args, 3)
        return asmgen.lhu(args[0], args[1], args[2])
    elif name == 'lhb':
        check_args(name, args, 3)
        return asmgen.sb(args[0], args[1], args[2])
    elif name == 'sh':
        check_args(name, args, 3)
        return asmgen.sh(args[0], args[1], args[2])
    elif name == 'sw':
        check_args(name, args, 3)
        return asmgen.sw(args[0], args[1], args[2])
    else:
        l = handle_extension(name, args)
        if l is None:
            print('そのような命令は存在しません: {}'.format(name))
            raise Exception('No Such Operation')
        else:
            # 拡張命令は複数命令に渡っている可能性がある。
            ret = bytes()
            for (name, args) in l:
                ret += asm(name, args)
            return ret


op_name_re = r'(?P<op_name>[a-zA-Z_](\w|\.)*)'
args_re = r'(?P<args>(((-|\w|\.|%|\(|\))+,)\s*)*(-|\w|\.|%|\(|\))+)?'  # 若干雑だが
comment_q = r'(#.*)?'
spaces = r'\s+'
spaces_star = r'\s*'
r = ''.join([
    spaces_star,
    tag_re,
    '?',
    spaces_star,
    op_name_re,
    spaces,
    args_re,
    spaces_star,
    comment_q,
    spaces_star,
    '$'
])
op_pat = re.compile(r)


class TestOperationRegex(unittest.TestCase):
    ''' does regex work correctly? '''

    def test_op_name_re(self):
        r = re.compile(op_name_re + '$')  # $はとりあえず仕方なく
        self.assertIsNotNone(r.match('mov'))
        self.assertIsNotNone(r.match('MOV'))
        self.assertEqual(r.match('mov').group('op_name'), 'mov')
        self.assertIsNone(r.match('0'))
        self.assertIsNone(r.match(' mov'))

    def test_args_re(self):
        r = re.compile(args_re + '$')
        self.assertIsNotNone(r.match('a, b, c, d, e,f,\tg, h'))
        self.assertIsNotNone(r.match('hoge'))
        self.assertIsNotNone(r.match(''))
        self.assertIsNotNone(r.match(r'%lo(msg)'))
        self.assertIsNone(r.match('a b c d'))
        self.assertIsNone(r.match('hoge,'))

    def test_all(self):
        self.assertIsNotNone(op_pat.match(
            'addi a1, a1,  %lo(msg)       # load msg(lo)'))
        self.assertIsNotNone(op_pat.match('jalr ra, puts'))
        self.assertIsNone(op_pat.match('_start:'))
        self.assertIsNotNone(op_pat.match(
            '1:	    auipc a1,     %pcrel_hi(msg) # load msg(hi)'))
        self.assertIsNone(op_pat.match('.globl _start'))

        m = op_pat.match('hoge: jalr ra, puts')
        self.assertEqual(m.group('tag_name'), 'hoge')
        self.assertEqual(m.group('op_name'), 'jalr')
        self.assertEqual(m.group('args'), 'ra, puts')


def parse_line(s):
    m = op_pat.match(s)
    if m is not None:
        op_name = m.group('op_name')
        # ここかっこよくやる方法わからん
        args = m.group('args').replace(' ', '').replace('\t', '').split(',')
        try:
            a = asm(op_name, args)
        except Exception as e:
            error_line(s)
            raise e
        return a
    elif debug:
        print('{} is ignored'.format(s))
    return None


def emit(output_file, assembly):
    output_file.write(assembly)


def main():
    global read_bytes

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='source file')
    parser.add_argument('--output', help='output file')

    args = parser.parse_args()
    filename = args.filename
    if args.output:
        output = args.output
    else:
        output = 'a.out'

    of = open(output, 'wb')

    for line in open(filename).readlines():
        l = line.strip()
        parse_tag_line(l)
        if parse_line(l) is not None:
            # あんま綺麗じゃないなあ
            read_bytes += len(parse_line(l))

    print(tags)
    asmgen.tags = tags

    for line in open(filename).readlines():
        a = parse_line(line.strip())
        emit(of, a)


def test():
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
