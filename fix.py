lb = 0x00020000
ub = 0x000213f0
with open("heap_file2", "w") as g:
    with open("heap_file", "r") as f:
        for l in f.readlines():
            l = l.strip()
            x = int(l, 16)
            if lb <= x <= ub:
                s = hex(x // 4)[2:]
                s = '0' * (8 - len(s)) + s
            else:
                s = l
            g.write(s)
            g.write("\n")

