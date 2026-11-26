"""Print the floor map of a piece of a room: fmap.py <prj2> <room> x0 x1 z0 z1   (heights in clicks above the given base)"""
import sys
import prj2_mesh as M


def show(prj, room, x0, x1, z0, z1, base=0, rooms=None):
    rooms = rooms or M.read_rooms(prj)[0]
    rm = [r for r in rooms if r.get('name') == room][0]
    print(room, 'pos', rm['pos'], ' rows z from', z1, 'down to', z0, ' cols x', x0, '..', x1)
    print('     ' + ' '.join('%5d' % x for x in range(x0, x1 + 1)))
    for z in range(z1, z0 - 1, -1):
        row = []
        for x in range(x0, x1 + 1):
            s = rm['sectors'].get((x, z))
            if not s:
                row.append('  .  ')
                continue
            f = s.get('floor', [0] * 4)
            c = s.get('ceil', [0] * 4)
            lo, hi = (min(f) - base) / 256, (max(f) - base) / 256
            t = ('%4.0f' % hi) if lo == hi else ('%2.0f~%-2.0f' % (lo, hi))
            row.append(('#' if s['wall'] else ' ') + t)
        print('%3d  ' % z + ' '.join(row))


if __name__ == '__main__':
    a = sys.argv
    show(a[1], a[2], int(a[3]), int(a[4]), int(a[5]), int(a[6]), int(a[7]) if len(a) > 7 else 0)
