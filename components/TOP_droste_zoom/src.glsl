// default Droste source: monochrome frame/grid/hatch with a red marker
uniform vec4 uT; // p (loop phase)
out vec4 fragColor;
const float TAU = 6.28318530718;
float box(vec2 p, vec2 b){ vec2 d = abs(p)-b; return length(max(d,0.))+min(max(d.x,d.y),0.); }
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = vUV.st; vec2 p = (uv-0.5)*vec2(res.x/res.y,1.0);
    vec3 c = vec3(0.02);
    // hatch field
    float h = abs(fract((p.x+p.y)*14.0)-0.5);
    c += vec3(0.16) * smoothstep(0.38,0.5,h) * step(0.18, length(p));
    // concentric rings
    float rg = abs(fract(length(p)*9.0 - 0.0)-0.5);
    c += vec3(0.5) * smoothstep(0.46,0.5,rg) * 0.5;
    // bold square frame
    float fr = abs(box(p, vec2(0.30,0.30)) - 0.02);
    c = mix(c, vec3(0.92,0.9,0.84), smoothstep(0.02,0.012,fr));
    // bars along the left side
    vec2 bp = p - vec2(-0.2, 0.0);
    float bars = step(abs(bp.x), 0.12) * step(0.5, fract(bp.y*20.0)) * step(abs(bp.y),0.22);
    c = mix(c, vec3(0.85), bars*0.7);
    // red marker orbiting (periodic)
    vec2 mp = 0.17*vec2(cos(TAU*uT.x), sin(TAU*uT.x));
    c = mix(c, vec3(1.0,0.08,0.04), smoothstep(0.035,0.028,length(p-mp)));
    // tick marks on the edge ring
    float a = atan(p.y,p.x);
    float t = step(0.9, fract(a*12.0/TAU)) * step(0.36, length(p)) * step(length(p),0.40);
    c = mix(c, vec3(0.9), t);
    fragColor = TDOutputSwizzle(vec4(c,1.0));
}
