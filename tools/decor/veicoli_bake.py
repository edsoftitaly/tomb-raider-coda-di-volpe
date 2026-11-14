"""Lights the painted elevations of a vehicle with a real render (14/11/2026).

decor/veicoli.py paints each vehicle as flat elevations (side, front, rear, plan) and projects them on the
lofted body. Here the same body, with those elevations as its colour, is rendered with a physically based
car paint under an overcast sky (three.js in headless Chromium, as the previews): the orthographic renders
from the five sides become the textures. So the paint mirrors sky and street along the real curvature of
the panels, the glass mirrors the sky, creases catch the light.

Needs node + playwright and /home/claude/vrender/three.module.min.js (the preview renderer). If the render
fails, bake() returns the elevations shaded by veicoli.finish() as before.
"""
import base64
import json
import os
import subprocess

import numpy as np
from PIL import Image
from scipy import ndimage

D = "/home/claude/vrender"
SS = 2            # the renders are made at twice the size of the textures

HTML = r"""<!doctype html><html><body style="margin:0;background:transparent">
<script type="module">
import * as THREE from './three.module.min.js';
const d=await (await fetch('bake.json')).json();
const r=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true,premultipliedAlpha:false});
r.setClearColor(0x000000,0);r.toneMapping=THREE.ACESFilmicToneMapping;r.toneMappingExposure=1.05;r.outputColorSpace=THREE.SRGBColorSpace;
document.body.appendChild(r.domElement);
const scene=new THREE.Scene();
// an overcast sky over a street: light from everywhere above, a line of dark houses on the horizon, grey asphalt
const c=document.createElement('canvas');c.width=1024;c.height=512;const g=c.getContext('2d');
let gr=g.createLinearGradient(0,0,0,256);gr.addColorStop(0,'#a9b3c0');gr.addColorStop(0.55,'#dfe4ea');gr.addColorStop(1,'#f4f5f6');g.fillStyle=gr;g.fillRect(0,0,1024,256);
gr=g.createLinearGradient(0,256,0,512);gr.addColorStop(0,'#77736c');gr.addColorStop(0.3,'#5e5b56');gr.addColorStop(1,'#3c3a37');g.fillStyle=gr;g.fillRect(0,256,1024,256);
let seed=7;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
for(let x=0;x<1024;){const w=18+rnd()*46,h=10+rnd()*34;g.fillStyle='rgb('+(70+rnd()*60|0)+','+(64+rnd()*50|0)+','+(58+rnd()*44|0)+')';g.fillRect(x,256-h,w,h+4);x+=w+rnd()*10;}
const sg=g.createRadialGradient(300,110,0,300,110,150);sg.addColorStop(0,'rgba(255,252,240,0.95)');sg.addColorStop(1,'rgba(255,252,240,0)');g.fillStyle=sg;g.fillRect(0,0,1024,256);
const env=new THREE.CanvasTexture(c);env.mapping=THREE.EquirectangularReflectionMapping;env.colorSpace=THREE.SRGBColorSpace;
const pm=new THREE.PMREMGenerator(r);scene.environment=pm.fromEquirectangular(env).texture;
const geo=new THREE.BufferGeometry();
geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(d.pos),3));
geo.setAttribute('uv',new THREE.BufferAttribute(new Float32Array(d.uv),2));
geo.setAttribute('normal',new THREE.BufferAttribute(new Float32Array(d.nrm),3));
const L=new THREE.TextureLoader();
const map=await L.loadAsync('bake_albedo.png');map.colorSpace=THREE.SRGBColorSpace;map.flipY=false;
const orm=await L.loadAsync('bake_orm.png');orm.flipY=false;
const mat=new THREE.MeshPhysicalMaterial({map:map,roughnessMap:orm,roughness:1.0,metalness:0.0,clearcoat:1.0,clearcoatMap:orm,clearcoatRoughness:0.06,envMapIntensity:1.15,side:THREE.DoubleSide});
scene.add(new THREE.Mesh(geo,mat));
const sun=new THREE.DirectionalLight(0xfff6e8,1.1);sun.position.set(-6,10,-4);scene.add(sun);
window.shot=(v)=>{
  r.setPixelRatio(1);r.setSize(v.w,v.h,false);r.domElement.style.width=v.w+'px';r.domElement.style.height=v.h+'px';
  const cam=new THREE.OrthographicCamera(-v.hw,v.hw,v.hh,-v.hh,0.1,60);
  cam.position.set(v.eye[0],v.eye[1],v.eye[2]);cam.up.set(v.up[0],v.up[1],v.up[2]);cam.lookAt(v.at[0],v.at[1],v.at[2]);
  r.render(scene,cam);return r.domElement.toDataURL('image/png');};
window.ready=true;
</script></body></html>"""

JS = r"""const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const pg=await b.newPage({viewport:{width:1600,height:900}});
const http=require('http'),fs=require('fs'),path=require('path');
const srv=http.createServer((q,s)=>{const f=path.join(__dirname,q.url.split('?')[0]);const t={'.js':'text/javascript','.html':'text/html','.png':'image/png','.json':'application/json'}[path.extname(f)]||'application/octet-stream';fs.readFile(f,(e,d)=>{if(e){s.writeHead(404);s.end();}else{s.writeHead(200,{'Content-Type':t});s.end(d);}});}).listen(8766);
pg.on('console',m=>console.log('page:',m.text()));pg.on('pageerror',e=>console.log('err:',e.message));
await pg.goto('http://localhost:8766/bake.html');await pg.waitForFunction('window.ready===true',null,{timeout:120000});
const V=JSON.parse(fs.readFileSync(path.join(__dirname,'bake_views.json')));
for(const v of V){const u=await pg.evaluate(v=>window.shot(v),v);fs.writeFileSync(path.join(__dirname,'bake_'+v.name+'.png'),Buffer.from(u.split(',')[1],'base64'));console.log('saved',v.name);}
await b.close();srv.close();})();"""


def _classify(rgb):
    """paint mask and glass mask of a flat elevation (the body colour is its most common colour)."""
    q = (rgb // 8).astype(int)
    keys = q[..., 0] * 1024 + q[..., 1] * 32 + q[..., 2]
    vals, counts = np.unique(keys, return_counts=True)
    k = vals[np.argmax(counts)]
    base = np.array([(k // 1024) * 8 + 4, ((k // 32) % 32) * 8 + 4, (k % 32) * 8 + 4], float)
    dist = np.abs(rgb - base).sum(axis=2)
    thr = max(10.0, min(70.0, 0.45 * float(np.abs(base - np.array((30, 38, 48.0))).sum())))
    paint = dist < thr
    lum = rgb.mean(axis=2)
    glass = (lum < 75) & (rgb[..., 2] > rgb[..., 0] + 4) & ~paint
    return paint, glass


def _fill_outside(a, alpha):
    """Colours the pixels outside the silhouette with the nearest colour inside it (faces at the edge of the
    silhouette would otherwise pick up the empty background)."""
    inside = alpha > 200
    if inside.all() or not inside.any():
        return a
    idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
    return a[idx[0], idx[1]]


def bake(key, v, images):
    from decor import veicoli as V
    B = v["body"]
    try:
        return _bake(V, B, key, images)
    except Exception as e:                                   # no renderer: painted light, as before
        print("  bake failed for %s (%s): painted light instead" % (key, e))
        V.BAKE = False
        try:
            return v["paint"](B)
        finally:
            V.BAKE = True


def _bake(V, B, key, images):
    names = [n for n in ("side", "side2", "front", "rear", "top") if n in images]
    if "side2" not in names:                                 # both flanks get their own light
        images = dict(images, side2=images["side"])
        names = ["side", "side2", "front", "rear", "top"]
    # atlas of the flat elevations
    pad = 4
    AW = max(images[n].shape[1] for n in names) + 2 * pad
    AH = sum(images[n].shape[0] + 2 * pad for n in names)
    alb = np.zeros((AH, AW, 3))
    orm = np.zeros((AH, AW, 3))
    off = {}
    y = 0
    for n in names:
        im = images[n][..., :3]
        h, w = im.shape[:2]
        big = np.pad(im, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        alb[y:y + h + 2 * pad, :w + 2 * pad] = big
        paint, glass = _classify(im)
        rough = np.where(paint, 0.34, np.where(glass, 0.06, 0.62))
        coat = np.where(paint, 1.0, np.where(glass, 0.6, 0.0))
        o = np.stack([coat * 255, rough * 255, np.zeros_like(rough)], axis=2)
        orm[y:y + h + 2 * pad, :w + 2 * pad] = np.pad(o, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        off[n] = (pad, y + pad)
        y += h + 2 * pad
    Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8)).save(os.path.join(D, "bake_albedo.png"))
    Image.fromarray(np.clip(orm, 0, 255).astype(np.uint8)).save(os.path.join(D, "bake_orm.png"))
    # the body, face by face, with the view each face takes its colour from
    faces = []
    orig = V.add_face

    def capture(m, body, q, view, out, region=None, uv=None):
        if view is not None and body is B:
            faces.append((np.array(q, float), view, np.array(out, float)))
    B.img_size = {k: a.shape[:2] for k, a in images.items()}
    V.add_face = capture
    try:
        B.mesh(extra_under=False)
    finally:
        V.add_face = orig
    pxf = {"side": lambda p: B.side_px(p[2], p[1]), "side2": lambda p: B.side_px(p[2], p[1]),
           "front": lambda p: B.front_px(p[0], p[1]), "rear": lambda p: B.rear_px(p[0], p[1]), "top": lambda p: B.top_px(p[0], p[2])}
    tris = []
    for q, view, out in faces:
        if abs(out[0]) > 0:
            out = np.array([out[0], 0, 0])
        P3 = q * np.array([1, 1, -1.0])                      # three.js is right-handed: mirror z
        o3 = out * np.array([1, 1, -1.0])
        uv = [((off[view][0] + pxf[view](p)[0]) / AW, (off[view][1] + pxf[view](p)[1]) / AH) for p in q]
        for (a, b, c) in ((0, 1, 2), (0, 2, 3)):
            nrm = np.cross(P3[b] - P3[a], P3[c] - P3[a])
            if np.linalg.norm(nrm) < 1e-10:
                continue
            idx = (a, b, c) if np.dot(nrm, o3) > 0 else (a, c, b)
            tris.append(([P3[i] for i in idx], [uv[i] for i in idx], nrm / np.linalg.norm(nrm) * (1 if np.dot(nrm, o3) > 0 else -1)))
    # smooth normals: the mean of the faces around each point
    acc = {}
    for pts, _, nrm in tris:
        for p in pts:
            k = tuple(np.round(p, 4))
            acc[k] = acc.get(k, 0) + nrm
    pos, uvs, nrms = [], [], []
    for pts, uv, nrm in tris:
        for p, t in zip(pts, uv):
            n = acc[tuple(np.round(p, 4))]
            n = n / (np.linalg.norm(n) + 1e-12)
            if np.dot(n, nrm) < 0.35:                        # a real edge (end caps): keep it sharp
                n = nrm
            pos.extend(p.tolist())
            uvs.extend([t[0], t[1]])
            nrms.extend(n.tolist())
    json.dump({"pos": pos, "uv": uvs, "nrm": nrms}, open(os.path.join(D, "bake.json"), "w"))
    yc = (B.H + 0.02 - 0.02) / 2
    H2, W2 = (B.H + 0.04) / 2, (B.W + 0.04) / 2
    cy = (B.H + 0.02 + (-0.02)) / 2
    views = []
    for n in names:
        h, w = images[n].shape[:2]
        v = {"name": n, "w": w * SS, "h": h * SS}
        if n in ("side", "side2"):
            sx = -1 if n == "side" else 1
            v.update(hw=B.L / 2, hh=H2, eye=[sx * 20, cy, 0], at=[0, cy, 0], up=[0, 1, 0])
        elif n in ("front", "rear"):
            sz = -1 if n == "front" else 1                   # the front of the car is at -z in three.js
            v.update(hw=W2, hh=H2, eye=[0, cy, sz * 20], at=[0, cy, 0], up=[0, 1, 0])
        else:
            v.update(hw=W2, hh=B.L / 2, eye=[0, 30, 0], at=[0, 0, 0], up=[0, 0, -1])
        views.append(v)
    del yc
    json.dump(views, open(os.path.join(D, "bake_views.json"), "w"))
    open(os.path.join(D, "bake.html"), "w").write(HTML)
    open(os.path.join(D, "bake.js"), "w").write(JS)
    r = subprocess.run(["node", "bake.js"], cwd=D, capture_output=True, text=True, timeout=240)
    if r.stdout.count("saved") != len(names):
        raise RuntimeError((r.stdout + r.stderr)[-300:])
    out = {}
    for n in names:
        flat = images[n][..., :3]
        h, w = flat.shape[:2]
        im = Image.open(os.path.join(D, "bake_%s.png" % n)).convert("RGBA").resize((w, h), Image.LANCZOS)
        a = np.asarray(im).astype(float)
        rgb, alpha = a[..., :3], a[..., 3]
        # the cameras are set so that every render lies as its elevation does; only the flank seen from +x
        # is mirrored (both flanks share the side convention: the front of the car on the left)
        if n == "side2":
            rgb, alpha = rgb[:, ::-1], alpha[:, ::-1]
        rgb = _fill_outside(rgb, alpha)
        if n != "top":
            # towards the road: the shadow under the body and a film of dust on the lower panels
            yy = (np.arange(h) / max(1, h - 1))[:, None] * np.ones((1, w))
            rgb = rgb * (1 - 0.30 * np.clip((yy - 0.84) / 0.16, 0, 1))[..., None]
            dust = np.clip((yy - 0.66) / 0.28, 0, 1) * (0.5 + V._fbm(h, w, h / 5.0, w / 6.0, 11)) * 0.14
            rgb = rgb * (1 - dust[..., None]) + np.array((128, 116, 98.0)) * dust[..., None]
        o = np.zeros((h, w, 4))
        o[..., :3] = np.clip(rgb, 0, 255)
        o[..., 3] = 255
        out[n] = V.grain(o, 5, 0.008)
    return out


if __name__ == "__main__":
    print(base64.b64encode(b"ok"))
