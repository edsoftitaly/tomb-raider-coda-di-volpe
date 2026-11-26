import sys, struct, collections
sys.path.insert(0,'.')
import nov26_lib as L, prj2_mesh as M, prj2_patch as P
def movs(src):
    head, top = P.load(src)
    rooms_p = dict(top)[b"TeRooms"]
    rooms,_ = M.read_rooms(src)
    pos_of={r["name"]:r["pos"] for r in rooms}
    out=[]; kinds=collections.Counter()
    def see(room,cid,p):
        kinds[cid]+=1
        if cid==b"TeMovTn3":
            _,o=L._leb_at(p); x,y,z,ry=struct.unpack("<4f",p[o:o+16]); rest=p[o+24:]; _,o2=L._leb_at(rest)
            t=struct.unpack("<I",rest[o2:o2+4])[0]; r2=rest[o2+4:]; ocb=struct.unpack("<h",r2[:2])[0]
            n=struct.unpack("<i",r2[17:21])[0]; nm=r2[21:21+n].decode('utf-8','replace')
            px,py,pz=pos_of[room]; out.append((t,nm,room,round((x+px*1024)/1024,1),round(y+py),round((z+pz*1024)/1024,1),ocb,r2[2:17].hex()))
        return p
    P.map_objects(rooms_p,see)
    return out,kinds
if __name__=="__main__":
    out,kinds=movs(sys.argv[1]); print(dict(kinds))
    c=collections.Counter(t for t,*_ in out); print(sorted(c.items()))
    for o in sorted(out):
        if o[1] and (len(sys.argv)<3 or any(k in o[1] for k in sys.argv[2:])): print(o)
