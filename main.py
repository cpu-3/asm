#!/usr/bin/env python
'''
 # ** instant ** assembler implementation

 ## 全体の構成
 fileを二回りするような実装。前提として一命令が4byteで構成されている。
 一般にアセンブラは、.s -> .oの変換を行い、.oファイルたちをリンカがリンクする
 というのが一般的だが、ファイルが複数になることはなさそうなことと、まぁそれほど
 大規模なプログラムはコンパイルしないだろうということ、命令の長さが決まっていることや
 展開される場所が決まっていることから、まぁ、こういう構成でええやろみたいな判断

 1. タグを前から探していき、その位置を記録する
 2. 前から順に、アセンブリを機械語に変換する。このとき、jmp命令の即値は
   適切に書き換える

 ## Prologue

 prologueとして、一般にOSがしそうな処理を最初に追加する。この部分はコンパイラ側で何をするかで
 少し挙動が変化する
 まず、spをメモリ領域の最下部に設定する。これも本来ここであるべきではないが、実質的なhook
 ```
   li sp, __builtin_stack_init
 ```
 entrypointへ、ジャンプするのは、単純に先頭にjmp命令を追加する
 ```
   j _min_caml_start
 ```

'''

import argparse
import re
import unittest

import asmgen
import extension
import hook
import utils


read_bytes = 0
emit_coe = False
tags = {}  # map[tag]int
use_place_holder = True

__builtin_stack_init = 0xf4240 - 4

tags['__builtin_stack_init'] = __builtin_stack_init

prologue = '''\
li sp, __builtin_stack_init
j _min_caml_start
'''

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
            raise Exception('Name error')
        tags[m.group('tag_name')] = read_bytes


def _solve_tag(name):
    if use_place_holder:
        return 0

    if name not in tags:
        print('{} は見つかりませんでした。'.format(name))
        raise Exception('Tag is not found')
    addr = tags[name]
    return addr


def solve_tag_relative(name):
    return str(_solve_tag(name) - read_bytes)


def solve_tag_absolute(name):
    return str(_solve_tag(name))


def check_args(name, args, length):
    if (len(args) == length):
        if (debug):
            print('{}: {}, {}'.format(hex(read_bytes)[2:], name, ','.join(args)))
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


def handle_args(args, relative=True):
    ret = []
    for arg in args:
        r = match_displacement(arg)
        if r is not None:
            # 再帰的にパターンが存在するかを（一応）確認する
            l = handle_args(r)
            ret += l
        elif not utils.is_special(arg):
            if relative:
                ret.append(solve_tag_relative(arg))
            else:
                ret.append(solve_tag_absolute(arg))
        else:
            ret.append(arg)
    return ret


def handle_hooked_instructions(name, arguments):
    args = handle_args(arguments, True)
    aargs = handle_args(arguments, False)
    if name == '_jal':
        check_args(name, args, 1)
        return hook.jal(args[0])
    elif name == '_jalr':
        check_args(name, args, 1)
        return hook.jalr(args[0])
    elif name == '_li':
        check_args(name, aargs, 2)
        return hook.li(aargs[0], aargs[1])
    elif name == '_add':
        check_args(name, args, 3)
        return hook.add(args[0], args[1], args[2])
    elif name == '_sub':
        check_args(name, args, 3)
        return hook.sub(args[0], args[1], args[2])
    else:
        return None


def hook_instructions(name, args):
    if name == 'jal':
        if len(args) == 1:
            return '_jal'
        else:
            return name
    elif name == 'jalr':
        if len(args) == 1:
            return '_jalr'
        else:
            return name
    elif name == 'li':
        if len(args) == 2 and utils.is_number(args[1]):
            return name
        else:
            return '_li'
    elif name == 'add':
        if len(args) == 3 and utils.is_number(args[2]):
            return '_add'
        else:
            return name
    elif name == 'sub':
        if len(args) == 3 and utils.is_number(args[2]):
            return '_sub'
        else:
            return name
    else:
        return name


def handle_extension(name, arguments):
    args = handle_args(arguments, True)
    if name == 'nop':
        check_args(name, args, 0)
        return extension.nop()
    elif name == 'li':
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
    elif name == 'j':
        check_args(name, args, 1)
        return extension.jump(args[0])
    elif name == 'jr':
        check_args(name, args, 1)
        return extension.jr(args[0])
    elif name == 'jrl':
        check_args(name, args, 1)
        return extension.jr(args[0])
    elif name == 'ret':
        check_args(name, args, 0)
        return extension.ret()
    elif name == 'call':
        check_args(name, args, 1)
        return extension.call(args[0])
    elif name == 'tail':
        check_args(name, args, 1)
        return extension.tail(args[0])
    elif name == 'subi':
        check_args(name, args, 3)
        return extension.subi(args[0], args[1], args[2])
    else:
        return handle_hooked_instructions(name, arguments)


def asm(name, arguments):
    args = handle_args(arguments)

    # 同名だが一定の解析で通常とは異なる動作をさせたい場合が存在する。
    # これをHookして、別の名前に書き換える
    name = hook_instructions(name, arguments)
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
    elif name == 'flw':
        check_args(name, args, 3)
        return asmgen.flw(args[0], args[1], args[2])
    elif name == 'fsw':
        check_args(name, args, 3)
        return asmgen.fsw(args[0], args[1], args[2])
    elif name == 'fadd.s':
        check_args(name, args, 3)
        return asmgen.fadd(args[0], args[1], args[2])
    elif name == 'fsub.s':
        check_args(name, args, 3)
        return asmgen.fsub(args[0], args[1], args[2])
    elif name == 'fmul.s':
        check_args(name, args, 3)
        return asmgen.fmul(args[0], args[1], args[2])
    elif name == 'fdiv.s':
        check_args(name, args, 3)
        return asmgen.fdiv(args[0], args[1], args[2])
    elif name == 'fsqrt.s':
        check_args(name, args, 2)
        return asmgen.sqrt(args[0], args[1])
    else:
        l = handle_extension(name, arguments)
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
space_args = '(' + spaces+args_re + ')'
no_args = spaces_star
args = '(' + space_args + '|' + no_args + ')'
r = ''.join([
    spaces_star,
    tag_re,
    '?',
    spaces_star,
    op_name_re,
    args,
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
        self.assertIsNotNone(op_pat.match(
            'ret'
        ))
        self.assertIsNone(op_pat.match('.globl _start'))
        self.assertIsNotNone(op_pat.match('	flw	fa5,%lo(.LC1)(a5)'))

        m = op_pat.match('hoge: jalr ra, puts')
        self.assertEqual(m.group('tag_name'), 'hoge')
        self.assertEqual(m.group('op_name'), 'jalr')
        self.assertEqual(m.group('args'), 'ra, puts')

dec_num = r'(-?[1-9][0-9]*|0)'
number = r'(?P<value>' + dec_num + ')'
r = ''.join([
    '^',
    spaces_star,
    tag_re,
    '?',
    spaces_star,
    '.word',
    spaces,
    number,
    spaces_star,
    comment_q,
    spaces_star,
    '$'
])
const_pat = re.compile(r)


class TestConstantRegex(unittest.TestCase):
    def test_constant(self):
        self.assertIsNotNone(const_pat.match('hoge:\t.word	1075838976'))
        self.assertIsNotNone(const_pat.match('\t.word       0 #zero'))
        self.assertIsNone(const_pat.match('hoge: jalr ra, puts'))

        m = const_pat.match('\t.word\t1075838976')
        self.assertEqual(m.group('value'), '1075838976')


def parse_line(s):
    # print('{}: {}'.format(read_bytes, s))
    m = op_pat.match(s)
    m2 = const_pat.match(s)
    if m is not None:
        op_name = m.group('op_name')
        # ここかっこよくやる方法わからん
        g = m.group('args')
        if g is None:
            args = []
        else:
            args = m.group('args').replace(' ', '').replace('\t', '').split(',')
        try:
            a = asm(op_name, args)
        except Exception as e:
            error_line(s)
            raise e
        return a
    elif m2 is not None:
        value = m.group('value')
        i = utils.check_and_trans_imm(value, 32)
        return utils.int2u32b(i)
    elif debug:
        print('{} is ignored'.format(s))
    return None


def emit(output_file, assembly):
    def hex2(x):
        s = hex(x)[2:]
        if len(s) == 1:
            return '0' + s
        else:
            return s

    if emit_coe:
        l = [hex2(x) for x in assembly]
        r = []
        if len(l) % 4 != 0:
            print('命令列のうち4byte alignedでないものが存在します')
            raise Exception('Alignment error')
        for i in range(len(l) // 4):
            r.append(''.join(l[4 * i: 4 * (i + 1)]))
        h = ',\n'.join(r)
        output_file.write((h + ',\n').encode('ascii'))
    else:
        output_file.write(assembly)


coe_prologue = b'''\
memory_initialization_radix=16;
memory_initialization_vector=
'''
coe_epilogue = b'''\
0;
'''

def main():
    global read_bytes, use_place_holder, emit_coe

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='source file')
    parser.add_argument('-c', '--coe', help='dump coe', action='store_true')
    parser.add_argument('--output', help='output file')

    args = parser.parse_args()
    filename = args.filename
    if args.output:
        output = args.output
    else:
        if args.coe:
            output = 'a.coe'
        else:
            output = 'a.out'
    of = open(output, 'wb')

    if args.coe:
        emit_coe = True
        of.write(coe_prologue)


    for line in prologue.split('\n'):
        a = parse_line(line.strip())
        if a is None:
            continue
        read_bytes += len(a)

    for line in open(filename).readlines():
        l = line.strip()
        parse_tag_line(l)
        if parse_line(l) is not None:
            # あんま綺麗じゃないなあ
            read_bytes += len(parse_line(l))

    print(tags)
    asmgen.tags = tags
    use_place_holder = False
    read_bytes = 0

    # prologue
    for line in prologue.split('\n'):
        a = parse_line(line.strip())
        if a is None:
            continue
        read_bytes += len(a)
        emit(of, a)

    for line in open(filename).readlines():
        a = parse_line(line.strip())
        if a is None:
            continue
        read_bytes += len(a)
        emit(of, a)
    
    # prologue
    if emit_coe:
        of.write(coe_epilogue)


def test():
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
