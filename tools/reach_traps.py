"""Dead ends: groups of places Lara can get into and never leave (sink components of the move graph), small ones only.
  reach_traps.py <prj2> [closed names,comma] [flip suffixes,comma]"""
import sys, collections
sys.setrecursionlimit(1000000)
import reach


def traps(w, start, banned=(), big=40):
    R = w.reach(start, banned=banned)
    adj = {n: [m for m in w.moves(n) if m in R] for n in R}
    # Tarjan, iterative
    index, low, on, st, comp, k = {}, {}, set(), [], {}, [0]
    for root in R:
        if root in index:
            continue
        work = [(root, 0)]
        while work:
            v, i = work[-1]
            if i == 0:
                index[v] = low[v] = k[0]; k[0] += 1; st.append(v); on.add(v)
            rec = False
            for j in range(i, len(adj[v])):
                u = adj[v][j]
                if u not in index:
                    work[-1] = (v, j + 1); work.append((u, 0)); rec = True; break
                elif u in on:
                    low[v] = min(low[v], index[u])
            if rec:
                continue
            if low[v] == index[v]:
                while True:
                    u = st.pop(); on.discard(u); comp[u] = v
                    if u == v:
                        break
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
    groups = collections.defaultdict(list)
    for n, c in comp.items():
        groups[c].append(n)
    out = []
    for c, ns in groups.items():
        if len(ns) > big:
            continue
        if all(comp[m] == c for n in ns for m in adj[n]):      # no way out of the group
            out.append(ns)
    return R, out


if __name__ == '__main__':
    prj = sys.argv[1]
    closed = set(sys.argv[2].split(',')) if len(sys.argv) > 2 and sys.argv[2] else set()
    flip = set(sys.argv[3].split(',')) if len(sys.argv) > 3 and sys.argv[3] else set()
    w = reach.World(prj, closed=closed, flip=flip, water=(lambda n, wet: False if n == 'W_00_01' and '_PIENO' not in flip else wet) if 'Marinello' in prj else None)
    ban = {c for c in w.cols if c[1] > 72 or c[0] > 84} if 'Marinello' in prj else set()
    R, t = traps(w, w.where('lara_start'), banned=ban)
    print(prj.split('/')[-1], 'closed', sorted(closed), 'flip', sorted(flip), 'reach', len(R), 'dead ends', len(t))
    for ns in sorted(t, key=lambda g: (w.nodes[g[0]]['rooms'][-1], g[0])):
        xs = [n[0] for n in ns]; zs = [n[1] for n in ns]
        sp = w.nodes[ns[0]]
        print('  %-18s x %d..%d z %d..%d  n=%d  y %d  %s' % (sp['rooms'][-1], min(xs), max(xs), min(zs), max(zs), len(ns), w.stand(ns[0]), 'water' if sp['water'] else ''))


def explain(w, ns):
    """why a one-sector dead end is (probably) not real: a solid static stands on it"""
    n = ns[0]
    x0, z0 = n[0] * 1024, n[1] * 1024
    for sb in w.sgrid.get((n[0], n[1]), []):
        if sb[0] < x0 + 824 and sb[3] > x0 + 200 and sb[2] < z0 + 824 and sb[5] > z0 + 200 and sb[4] > w.stand(n) + 100 and sb[1] < w.stand(n) + 700:
            return 'static %d on it' % sb[6]
    nb = []
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for m in w.bycol.get((n[0] + dx, n[1] + dz), []):
            nb.append('%+.0f' % ((w.stand(m) - w.stand(n)) / 256))
    return 'neighbours (clicks) ' + ' '.join(nb) + ' ceil %+.0f' % ((w.nodes[n]['cmax'] - w.stand(n)) / 256)
