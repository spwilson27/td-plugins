exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
exec(open(os.path.join(LIB, 'components/_gbuf/gbuf.py')).read())
s = begin('TOP_normal_shade')
R = ('1280', '720')

ex = example(s, 1, 'Matcap-shade a Render TOP normal buffer',
             'A Render TOP draws Sphere / Torus / Box POPs with a GLSL MAT that writes view-space normals to an extra\ncolour buffer. TOP_normal_shade looks the normals up in its built-in matcap and tints with the G-buffer colour.\nTry: Matcaprotate, Colormix, plug your own matcap image into in2.')
gb = make_gbuffer(s, res=R, prefix='ex1_')
f = instance(ex, 'TOP_normal_shade')
f.inputConnectors[0].connect(gb['normal']); f.inputConnectors[2].connect(gb['color'])
f.par.Background = 'color'
out(ex, 1, f)

ex = example(s, 2, 'Key / fill / rim lights, matcap from a picture',
             'Mode = lights shades the normals with a key light, a cool fill and a rim light (Lights page).\nTry: Keyazimuth / Keyelevation, Rimintensity, Rimpower, Specamount, Wrap.\nExample 3 swaps in an image as a matcap.')
gb = make_gbuffer(s, res=R, prefix='ex2_')
f = instance(ex, 'TOP_normal_shade')
f.inputConnectors[0].connect(gb['normal'])
f.par.Mode = 'lights'; f.par.Rimintensity = 1.0; f.par.Keyazimuth = 40; f.par.Colormix = 0
out(ex, 2, f)

ex = example(s, 3, 'An image as matcap',
             'Any sphere-on-black image works as a matcap in in2; the normal XY picks the pixel.\nHere a small GLSL TOP paints a gold matcap. Matcapflip / Matcaprotate re-orient it.')
gb = make_gbuffer(s, res=R, prefix='ex3_')
mc = ex.create(td.glslTOP, 'matcap', row=1)
dat = s.create(td.textDAT, 'ex3_matcap_code'); dat.text = """out vec4 fragColor;
void main(){
    vec2 p = vUV.st * 2.0 - 1.0; float r = length(p);
    vec3 n = vec3(p, sqrt(max(0.0, 1.0 - r * r))); if (r > 1.0) n = vec3(normalize(p), 0.0);
    vec3 R = reflect(vec3(0, 0, -1), n);
    float sky = smoothstep(-0.2, 0.9, R.y);
    vec3 c = mix(vec3(0.25, 0.12, 0.04), vec3(1.0, 0.8, 0.4), sky);
    c += vec3(1.0, 0.95, 0.8) * smoothstep(0.88, 0.93, dot(R, normalize(vec3(-0.5, 0.7, 0.5))));
    c *= 0.55 + 0.6 * pow(1.0 - n.z, 0.6);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}"""
mc.par.pixeldat = dat; mc.par.outputresolution = 'custom'; mc.par.resolutionw = 512; mc.par.resolutionh = 512
f = instance(ex, 'TOP_normal_shade')
f.inputConnectors[0].connect(gb['normal']); f.inputConnectors[1].connect(mc)
f.par.Colormix = 0
out(ex, 3, f)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
