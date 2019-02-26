l = []


def add(name, size):
    global l
    l.append((name, size))


add("n_objects", 4)
add("dummy", 12 * 4)
add("objects", 60 * 4)
add("screen", 3 * 4)
add("viewpoint", 3 * 4)
add("light", 3 * 4)
add("beam", 1 * 4)
add("dummy", 4)
add("and_net", 50 * 4)
add("dummy", 4)
add("or_net", 1 * 4)
add("solver_dist", 1 * 4)
add("intsec_rectside", 1 * 4)
add("tmin", 1 * 4)
add("intersection_point", 3 * 4)
add("intersected_object_id", 1 * 4)
add("nvector", 3 * 4)
add("texture_color", 3 * 4)
add("diffuse_ray", 3 * 4)
add("rgb", 3 * 4)
add("image_size", 2 * 4)
add("image_center", 2 * 4)
add("scan_pitch", 1 * 4)
add("startp", 3 * 4)
add("startp_fast", 3 * 4)
add("screenx_dir", 3 * 4)
add("screeny_dir", 3 * 4)
add("screenz_dir", 3 * 4)
add("ptrace_dirvec", 3 * 4)
add("dummy", 4 * 2)
add("dirvecs", 5 * 4)
add("dummy", 3 * 4 + 60 * 4)
add("light_dirvec", 4 * 2)
add("dummy", 2 * 4 + 3 * 4 + 4)
add("reflections", 180 * 4)
add("n_reflections", 1 * 4)


dic = {}
base = 0x10 * 4
for x in l:
    dic[x[0]] = base
    base += x[1]

def get(name):
    return dic[name[9:]]


if __name__ == '__main__':
    base = 0x10 * 4
    print("[",end="")
    for x in l:
        print("(\"", x[0], "\",",  base // 4, ");", sep="")
        base += x[1]
    print("]",end="")
