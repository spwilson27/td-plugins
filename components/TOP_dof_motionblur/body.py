c = new_comp(COMP)
add_pars(c, [
    ('Speed', 'float', 1.0, 0, 8),
    ('Depthmode', 'menu', [('auto', 'Auto (in2, else radial)'), ('in2', 'in2 TOP'), ('luma', 'Luminance'), ('radial', 'Radial mask')], 0),
    ('Invertdepth', 'toggle', 0),
    ('Focus', 'float', 0.5, 0, 1),
    ('Range', 'float', 0.08, 0, 0.5),
    ('Falloff', 'float', 0.4, 0.02, 1),
    ('Maxblur', 'float', 28, 0, 100),
    ('Quality', 'int', 64, 8, 160),
    ('Boost', 'float', 2.0, 0, 20),
    ('Blades', 'int', 6, 0, 12),
    ('Bladerot', 'float', 0.2, 0, 6.28),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
add_pars(c, [
    ('Mbactive', 'toggle', 1),
    ('Shutter', 'float', 0.55, 0, 0.97),
    ('Velscale', 'float', 1.0, 0, 20),
    ('Velsamples', 'int', 24, 4, 63),
    ('Reset', 'pulse'),
], page='Motion')
add_pars(c, [('Showdepth', 'toggle', 0), ('Showcoc', 'toggle', 0)], page='Output')
loop_pars(c, beats=8)
P = 'parent().par.'
PH = "(%s if parent().par.Timesource=='phase' else absTime.seconds*parent().par.Speed/%s) %% 1.0" % (EXTPH, LENEXPR)
PH = '(' + PH + ')'
HAS1 = "1 if parent().inputConnectors[0].connections else 0"
HAS2 = "1 if parent().inputConnectors[1].connections else 0"
HAS3 = "1 if parent().inputConnectors[2].connections else 0"
res_chop(c)
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2'); i3 = c.create(td.inTOP, 'in3')
add_mod(c, 'in4')
dcol = glsl(c, 'defcolor', rd(COMP, 'src.glsl'), vecs=[('uA', [PH, 0, 0, 0])], res=True)
ddep = glsl(c, 'defdepth', rd(COMP, 'src.glsl'), vecs=[('uA', [PH, 1, 0, 0])], res=True)
def sw(nm, a, b, expr):
    s = c.create(td.switchTOP, nm); s.inputConnectors[0].connect(a); s.inputConnectors[1].connect(b)
    s.par.index.expr = expr
    setres(s); s.par.format = 'rgba16float'
    return s
src = sw('src', dcol, i1, HAS1)
dsrc = sw('depthsrc', ddep, i2, HAS2)
prep = glsl(c, 'prep', rd(COMP, 'prep.glsl'), inputs=[src, dsrc], res=True,
            vecs=[('uA', [P + 'Depthmode.menuIndex', HAS1, HAS2, '1 if ' + P + 'Invertdepth else 0'])])
FOC = "min(1,max(0,%sFocus+%sModamount*%s*0.5))" % (P, P, MOD('band1'))
RS = "op('res')['h']/720.0"
dof = glsl(c, 'dof', rd(COMP, 'dof.glsl'), inputs=[src, prep], res=True, vecs=[
    ('uA', [FOC, P + 'Range', P + 'Falloff', P + 'Maxblur']),
    ('uB', [P + 'Quality', P + 'Boost', P + 'Blades', P + 'Bladerot']),
    ('uC', [RS, 0, 0, 0])])
dof.par.inputextenduv = 'hold'
mb = glsl(c, 'mblur', rd(COMP, 'mblur.glsl'), inputs=[dof, i3], res=True,
          vecs=[('uA', [P + 'Velscale*' + P + 'Mbactive', P + 'Velsamples', HAS3, 0])])
mb.par.inputextenduv = 'hold'
blk = c.create(td.constantTOP, 'blank'); setres(blk)
blk.par.format = 'rgba16float'; blk.par.colorr = blk.par.colorg = blk.par.colorb = 0; blk.par.alpha = 1
fb = c.create(td.feedbackTOP, 'feedback'); fb.inputConnectors[0].connect(blk)
fb.par.format = 'rgba16float'
fb.par.reset.expr = P + 'Reset'
acc = glsl(c, 'accum', rd(COMP, 'accum.glsl'), inputs=[fb, mb], res=True,
           vecs=[('uA', [P + 'Shutter', '1 if ' + P + 'Mbactive else 0', 0, 0])])
nul = c.create(td.nullTOP, 'accum_out'); nul.inputConnectors[0].connect(acc)
fb.par.top = nul
vis = glsl(c, 'viewsel', """out vec4 fragColor;
uniform vec4 uV; // showdepth, showcoc, focus, range
uniform vec4 uW; // falloff
void main(){
  vec2 uv = vUV.st;
  vec3 col = texture(sTD2DInputs[0], uv).rgb;
  float d = texture(sTD2DInputs[1], uv).r;
  if(uV.x > 0.5) col = vec3(d);
  if(uV.y > 0.5){ float x = smoothstep(0.0,1.0,(abs(d-uV.z)-uV.w)/max(uW.x,1e-3)); col = mix(vec3(0.05,0.9,0.2), vec3(1.0,0.1,0.1), x) * 0.7+0.0; }
  fragColor = TDOutputSwizzle(vec4(col,1.0));
}
""", inputs=[nul, prep], res=True, vecs=[
    ('uV', ['1 if ' + P + 'Showdepth else 0', '1 if ' + P + 'Showcoc else 0', FOC, P + 'Range']),
    ('uW', [P + 'Falloff', 0, 0, 0])])
finish_v2(c, COMP, vis, src, extra_outs=[(prep, 'depth')])
report(c)
