// Initial state: A=1, B=seed. Input0 = optional mask (in1), uHasIn selects it.
out vec4 fragColor;
uniform float uHasIn;
uniform vec2 uRes;
uniform float uSeed;
float hash(vec2 p){ p = fract(p*vec2(443.897,441.423)+uSeed*0.137); p += dot(p,p.yx+19.19); return fract((p.x+p.y)*p.x*p.y*0.0001+p.x*p.y); }
float hash2(vec2 p){ vec3 q = fract(vec3(p.xyx)*vec3(.1031,.1030,.0973)+uSeed*0.011); q += dot(q,q.yzx+33.33); return fract((q.x+q.y)*q.z); }
void main(){
    vec2 uv = vUV.st;
    float b = 0.0;
    if (uHasIn > 0.5) {
        vec3 c = texture(sTD2DInputs[0], uv).rgb;
        b = step(0.35, dot(c, vec3(0.333)));
    } else {
        // random blobs on a coarse grid, plus a central seed
        float cells = 14.0;
        vec2 g = uv*cells*vec2(uRes.x/uRes.y,1.0);
        vec2 id = floor(g), f = fract(g)-0.5;
        float r = hash2(id);
        vec2 off = (vec2(hash2(id+7.3), hash2(id+13.1))-0.5)*0.5;
        if (r > 0.82) b = 1.0 - step(0.0, length(f-off) - (0.12+0.14*hash2(id+3.7)));
        b = max(b, 1.0 - step(0.0, length((uv-0.5)*uRes)/40.0 - 1.0));
    }
    fragColor = TDOutputSwizzle(vec4(1.0 - 0.5*b, b, 0.0, 1.0));
}
