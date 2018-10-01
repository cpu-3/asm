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


read_byte = 0
tags = {} # map[tag]int

debug = True

tag_re = r'((?P<tag_name>[a-zA-Z_][\w|.]*):)'
r = r'^\s*' + tag_re + r'.*$'
tag_pat = re.compile(r)
def parse_tag_line(s):
    m = tag_pat.match(s)
    if m is not None:
        tags[m.group('tag_name')] = read_byte


def check_args(name, args, length):
    if (len(args) == length):
        return

    print('{} should have {} args. But got {}'.format(name, length, len(args)))
    print('  -> {} {}', name, ','.join(args))
    raise(Exception('Syntax Error'))


def asm(name, args):
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
    else:
        print('そのような命令は存在しません: {}'.format(name))
        raise Exception('No Such Operation')


op_name_re = r'(?P<op_name>[a-zA-Z_](\w|\.)*)'
args_re = r'(?P<args>(((-|\w|\.|%|\(|\))+,)\s*)*(-|\w|\.|%|\(|\))+)?' # 若干雑だが
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

class TestRegexes(unittest.TestCase):
    ''' does regex work correctly? '''

    def test_op_name_re(self):
        r = re.compile(op_name_re + '$') # $はとりあえず仕方なく
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
        self.assertIsNotNone(op_pat.match('addi a1, a1,  %lo(msg)       # load msg(lo)'))
        self.assertIsNotNone(op_pat.match('jalr ra, puts'))
        self.assertIsNone(op_pat.match('_start:'))
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
        a = asm(op_name, args)
        return a
    elif debug:
        print('{} is ignored'.format(s))
    return None


def emit(output_file, assembly):
    output_file.write(assembly)


def main():
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
        parse_tag_line(line.strip())

    for line in open(filename).readlines():
        a = parse_line(line)
        emit(of, a)

def test():
    unittest.main(verbosity=2)

if __name__ == '__main__':
    main()
