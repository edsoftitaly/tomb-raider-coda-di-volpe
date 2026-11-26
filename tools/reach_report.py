import sys, collections, reach
def report(prj, flip, closed, start='lara_start', steps=(), show_rooms=True, banned=()):
    w = reach.World(prj, flip=flip, closed=closed, step_extra=steps)
    s = w.where(start)
    R = w.reach(s, banned=banned)
    got = []
    for o in w.objs:
        if o['kind'] != 'mov':
            continue
        n = w.node_at(*o['pos'])
        tag = 'REACHED' if n in R else ('no node' if n is None else '-')
        got.append((tag, o['name'] or 'id%d' % o['type'], o['room'], [round(v) for v in o['pos']]))
    rooms = collections.Counter()
    for n in R:
        rooms[w.nodes[n]['rooms'][-1]] += 1
    return w, R, got, rooms
if __name__ == '__main__':
    pass
