exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# SDF snippet helpers: N = instance with parameters ('=expr' sets an expression), W = wire SDF out -> in, R = render -> exampleN
def N(ex, name, **kw):
    i = instance(ex, name)
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith('='): i.par[k].expr = v[1:]
        else: i.par[k] = v
    return i
def W(a, b, idx=0): connect(a, b, 0, idx)
def R(ex, scene, n, res=(960, 540), **kw):
    r = N(ex, 'SDF_render', Resolutionw=res[0], Resolutionh=res[1], **kw)
    W(scene, r); out(ex, n, r); return r
def ORBIT(ex, dist=5.0, height=1.6, speed=0.4, fov=60, target_y=0.0):
    cam = ex.create(cameraCOMP, 'cam')
    cam.par.tx.expr = '%g*math.sin(absTime.seconds*%g)' % (dist, speed)
    cam.par.tz.expr = '%g*math.cos(absTime.seconds*%g)' % (dist, speed)
    cam.par.ty = height
    cam.par.ry.expr = 'math.degrees(absTime.seconds*%g)' % speed
    cam.par.rx = -math.degrees(math.atan2(height - target_y, dist))
    cam.par.fov = fov
    return cam

s = begin('SDF_from_POP')
ex = example(s, 1, 'Liquid flock: POP_boids as metaballs', 'POP_boids points go into SDF_from_POP (Mode = points): every boid becomes a sphere, smooth-unioned into one liquid blob, coloured by the Color attribute of the flock.\nThe points arrive in the shader as a buffer, so the flock moves without any recompile. Try Radius, Blend (smooth K), Grid Resolution.')
b = N(ex, 'POP_boids', Maxboids=900, Boundsize=2.2, Sepradius=0.4, Cohesion=2.5, Cohradius=2.5)
fp = N(ex, 'SDF_from_POP', Radius=0.17, Blend=0.4, Gridres=40); connect(b, fp, 0, 0)
f = N(ex, 'SDF_plane', Offset=-3.0, Colorr=0.3, Colorg=0.3, Colorb=0.34, Checker=False)
c = N(ex, 'SDF_combine', Smooth=0.0); W(fp, c, 0); W(f, c, 1)
r = R(ex, c, 1, Reflectivity=0.25, Shadows=6.0, Maxdist=40)
r.par.Camera = ORBIT(ex, dist=11.5, height=3.6, speed=0.3, fov=50)
ex = example(s, 2, 'A baked mesh in an SDF scene', 'Mode = mesh voxelizes a Torus POP into a 3D distance texture (Resolution, Padding, Band). It is lossy, so it needs a closed mesh, but then it behaves like any SDF primitive: here a smooth union with a gyroid.\nUpdate = once bakes on load, on Bake Now and when the input is rewired; Every frame re-bakes a moving mesh.')
tor = ex.create(torusPOP, 'torus'); tor.par.radx = 1.15; tor.par.rady = 0.32; tor.par.cols = 96; tor.par.rows = 48; tor.par.orient = 'z'
fm = N(ex, 'SDF_from_POP', Mode='mesh', Resolution=112, Colorr=0.95, Colorg=0.45, Colorb=0.25); connect(tor, fm, 0, 0)
gy = N(ex, 'SDF_gyroid', Boundradius=0.95, Thickness=0.3, Colorr=0.3, Colorg=0.6, Colorb=0.95)
cm = N(ex, 'SDF_combine', Smooth=0.12); W(fm, cm, 0); W(gy, cm, 1)
R(ex, cm, 2, Shadows=10.0)
ex = example(s, 3, 'An infinite field of baked meshes', 'The baked torus goes through SDF_repeat (grid, infinite). The volume repeats cheaply because every cell only samples the same texture; outside its bounds the field falls back to the distance to the box, so rays still converge.\nThe camera flies through; raise Resolution on SDF_from_POP for crisper surfaces.')
tor3 = ex.create(torusPOP, 'torus'); tor3.par.radx = 0.8; tor3.par.rady = 0.28; tor3.par.cols = 96; tor3.par.rows = 48; tor3.par.orient = 'z'
fm3 = N(ex, 'SDF_from_POP', Mode='mesh', Resolution=96, Padding=0.15, Colorr=0.85, Colorg=0.85, Colorb=0.9); connect(tor3, fm3, 0, 0)
rp = N(ex, 'SDF_repeat', Mode='grid', Spacingx=3.2, Spacingy=3.2, Spacingz=3.2, Colorvary=0.5); W(fm3, rp)
cam = ex.create(cameraCOMP, 'cam'); cam.par.tx = 1.6; cam.par.ty = 1.6; cam.par.tz.expr = '1.6-absTime.seconds*0.7'; cam.par.ry = 180; cam.par.fov = 70
r = R(ex, rp, 3, Fog=0.07, Shadows=0.0, Stepscale=0.8, Maxdist=40)
r.par.Camera = cam
for c_ in s.findChildren(type=COMP, depth=1):
    if c_.par.externaltox.eval(): c_.par.reloadcustom = False
finish(s)
