# sdflib: SDF wire format v1 (see CONVENTIONS.md "SDF section"). Stored in a Text DAT named `sdflib`
# in every SDF_ component and used as `op('sdflib').module`.
#
# Payload text (what travels on an SDF DAT wire):
#   #SDF 1
#   @node n123 sphere          one record per node, upstream nodes first
#   @vals                      parameter values, one vec4 per line (animated; NOT part of the shader code)
#   0.5 0 0 0
#   @code                      GLSL; vec4 sdf_<id>(vec3 p) returns (distance, albedo rgb)
#   vec4 sdf_n123(vec3 p){ return vec4(length(p)-P_n123_0.x, P_n123_1.xyz); }
#   @end
#   @scene n123                id of the node whose function is the final scene
MAXV = 128

def _f(x):
    return '%.7g' % float(x)

def parse(text):
    nodes, scene, cur, mode = [], None, None, None
    for line in (text or '').splitlines():
        if line.startswith('@node'):
            w = line.split()
            if len(w) < 2: continue
            cur = dict(id=w[1], kind=w[2] if len(w) > 2 else '', vals=[], code=[]); mode = None
        elif line.startswith('@vals'):
            mode = 'v'
        elif line.startswith('@code'):
            mode = 'c'
        elif line.startswith('@end'):
            if cur is not None:
                cur['code'] = '\n'.join(cur['code']); nodes.append(cur)
            cur, mode = None, None
        elif line.startswith('@scene'):
            w = line.split()
            if len(w) > 1: scene = w[1]
        elif cur is not None and mode == 'v' and line.strip():
            try:
                v = [float(x) for x in line.split()[:4]]
            except ValueError:
                v = [0.0]
            cur['vals'].append(tuple(v + [0.0] * (4 - len(v))))
        elif cur is not None and mode == 'c':
            cur['code'].append(line)
    ids = set(n['id'] for n in nodes)
    if scene not in ids:
        scene = nodes[-1]['id'] if nodes else None
    return nodes, scene

def emit(nodes, scene):
    o = ['#SDF 1']
    for n in nodes:
        o.append('@node %s %s' % (n['id'], n.get('kind', '')))
        o.append('@vals')
        for v in n['vals']:
            o.append(' '.join(_f(x) for x in v))
        o.append('@code')
        o.append(n['code'])
        o.append('@end')
    o.append('@scene %s' % scene)
    return '\n'.join(o) + '\n'

SPHERE = ("vec4 sdf_@ID@(vec3 p){ return vec4(length(p) - P_@ID@_0.x, P_@ID@_1.xyz); }")
BOX = ("vec4 sdf_@ID@(vec3 p){ vec3 q = abs(p) - P_@ID@_0.xyz + P_@ID@_0.w;\n"
       "  return vec4(length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - P_@ID@_0.w, P_@ID@_1.xyz); }")

def default_payload(which='A'):
    if which == 'B':
        n = dict(id='d1', kind='box', vals=[(0.5, 0.5, 0.5, 0.08), (0.9, 0.35, 0.25, 0)], code=BOX.replace('@ID@', 'd1'))
    else:
        n = dict(id='d0', kind='sphere', vals=[(0.7, 0, 0, 0), (0.85, 0.85, 0.85, 0)], code=SPHERE.replace('@ID@', 'd0'))
    return [n], n['id']

def build_node(owner, kind, ins, code, vals, defaults='AB'):
    """Payload text for one node. ins: list of In DAT ops (or None). `code` uses @ID@ for this node's id,
    @A@/@B@ for the upstream scene ids. vals: list of 4-sequences (the node's parameters this frame)."""
    nid = 'n%d' % owner.id
    merged, seen, ups = [], set(), []
    for i, inp in enumerate(ins):
        nodes, scene = parse(inp.text if inp is not None else '')
        if not nodes:
            nodes, scene = default_payload(defaults[i])
        for n in nodes:
            if n['id'] not in seen:
                seen.add(n['id']); merged.append(n)
        ups.append(scene)
    c = code.replace('@ID@', nid)
    for i, s in enumerate(ups):
        c = c.replace('@%s@' % 'AB'[i], 'sdf_' + s)
    merged.append(dict(id=nid, kind=kind, vals=[tuple(float(x) for x in v) for v in vals], code=c))
    return emit(merged, nid)

def write_node(dat, owner, kind, ins, code, vals, defaults='AB'):
    dat.clear()
    dat.write(build_node(owner, kind, ins, code, vals, defaults))

def assemble(text, tb=False):
    """-> (glsl, vals). glsl declares `uniform vec4 uSdf[MAXV]`, the P_<id>_<k> macros, every node
    function and `vec4 sdScene(vec3 p)`. It depends only on the payload structure (never on values)."""
    nodes, scene = parse(text)
    if not nodes:
        nodes, scene = default_payload('A')
    defs, funcs, vals = [], [], []
    for n in nodes:
        for k, v in enumerate(n['vals']):
            defs.append(('#define P_%s_%d texelFetch(uSdf, %d)' if tb else '#define P_%s_%d uSdf[%d]') % (n['id'], k, len(vals))); vals.append(v)
        funcs.append(n['code'])
    if len(vals) > MAXV:
        raise Exception('SDF scene has %d parameter vec4s (max %d)' % (len(vals), MAXV))
    glsl = '\n'.join([('uniform samplerBuffer uSdf;' if tb else 'uniform vec4 uSdf[%d];' % MAXV)] + defs + funcs + ['vec4 sdScene(vec3 p){ return sdf_%s(p); }' % scene]) + '\n'
    return glsl, vals

def write_shader(dat, in_text, template, tb=False):
    """Script DAT body: shader = template with //@@SDF@@ replaced; rewritten only when it changes,
    so animating parameters never touches the shader DAT."""
    glsl, _ = assemble(in_text, tb)
    full = template.replace('//@@SDF@@', glsl)
    if dat.text != full:
        dat.clear(); dat.write(full)

def write_vals(dat, in_text):
    """Script DAT body: the parameter values as a MAXV x 4 table (feeds a DAT to CHOP -> uniform array uSdf)."""
    _, vals = assemble(in_text)
    vals = list(vals) + [(0, 0, 0, 0)] * (MAXV - len(vals))
    dat.clear()
    for v in vals:
        dat.appendRow([_f(x) for x in v])

def camv(cam, t, speed):
    """Camera constants for the raymarchers (16 floats): pos.xyz, tan(fov/2) | right.xyz, fov mode (0 horizontal,
    1 vertical) | up.xyz, 0 | forward.xyz, 0. `cam` = Camera COMP or None (built-in orbiting default camera)."""
    import math
    def nz(v):
        l = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / l for x in v]
    if cam is None:
        a = math.radians(t * speed) + 0.6
        pos = [5.0 * math.sin(a), 1.9, 5.0 * math.cos(a)]
        f = nz([-pos[0], 0.1 - pos[1], -pos[2]])
        r = nz([f[2] * -1.0 * -1.0 * 0 + (f[1] * 0 - f[2] * 1.0) * -1.0, 0.0, 0.0]) if False else nz([-f[2], 0.0, f[0]])
        u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]]
        # right = f x up(0,1,0) = (-f.z, 0, f.x); up = right x f
        u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]]
        fov, mode = 55.0, 0
    else:
        m = cam.worldTransform
        pos = [m[0, 3], m[1, 3], m[2, 3]]
        r = nz([m[0, 0], m[1, 0], m[2, 0]]); u = nz([m[0, 1], m[1, 1], m[2, 1]]); f = nz([-m[0, 2], -m[1, 2], -m[2, 2]])
        fov = cam.par.fov.eval()
        mode = 1 if cam.par.viewanglemethod.eval() == 'vertfov' else 0
    return pos + [math.tan(math.radians(fov) / 2)] + r + [mode] + u + [0] + f + [0]
