// per-instance data, one pixel per glyph instance. uD.x selects channel set:
// 0 translate, 1 rotate(deg), 2 scale, 3 color, 4 uv offset, 5 uv scale
uniform vec4 uA; // N, layers, mode, loopPhase(unwrapped)
uniform vec4 uB; // size, spacing, amount, stretch
uniform vec4 uC; // beatsPerLoop, autoOn, trigEnv, depth
uniform vec4 uD; // channel, accentAmt, decay, seed
uniform vec4 uE; // tint rgb, -
uniform vec4 uF; // accent rgb, -
out vec4 fragColor;
const float TAU = 6.28318530718;
float h1(float n){ return fract(sin(n*127.1+uD.w*11.7)*43758.5453); }
vec3 h3(float n){ return vec3(h1(n), h1(n+17.3), h1(n+41.9)); }
void main(){
    float N = uA.x, L = uA.y; int mode = int(uA.z+0.5);
    float p = uA.w;
    float i = floor(vUV.s * uTDOutputInfo.res.z);
    float g = mod(i, N);
    float l = floor(i / N);
    float xn = (g + 0.5) / N;
    float gw = 0.5 * uB.x * uB.y;                 // glyph pitch in world units
    vec3 base = vec3((g + 0.5 - 0.5*N) * gw, 0., 0.);
    vec3 pos = base, rot = vec3(0.), scl = vec3(uB.x);
    vec2 uvs = vec2(1.0/N, 1.0);
    vec2 uvo = vec2(g/N, 0.);
    float br = 1.;
    float accent = 0.;
    float amt = uB.z;
    float pick = step(1. - uD.y, h1(g + 91.));
    if(mode == 0){
        float bp = fract(p * uC.x);
        float env = max(uC.y * exp(-uD.z * bp), uC.z);
        vec3 r = h3(g) - 0.5, r2 = h3(g + 33.) - 0.5;
        pos += vec3(r.x*8., r.y*5., r.z*7.) * env * amt;
        rot = r2 * 360. * env * amt;
        scl *= 1. + env * 0.6 * (h1(g+5.) - 0.3);
        accent = pick * smoothstep(0.05, 0.6, env);
    } else if(mode == 1){
        float s = 0.5 + 0.5 * cos(TAU * p);
        float d = (xn - s) * N;
        float w = exp(-d*d / 6.0);
        float us = mix(1.0, 0.06, w);
        scl.x *= 1. + w * uB.w;
        uvs.x = us / N;
        uvo.x = g/N + (1.0 - us) * 0.5 / N;
        pos.x += sign(d) * w * gw * uB.w * 0.35;
        accent = pick * w;
        br = 0.5 + 0.5 * w;
    } else if(mode == 2){
        float a = TAU * p;
        vec3 q = base * 0.35;
        vec3 n = vec3(sin(a + q.x*1.3 + sin(2.*a + q.x)),
                      sin(2.*a + q.x*0.9 + 1.7),
                      cos(a + q.x*0.7 + sin(3.*a)));
        pos += n * amt * vec3(0.4, 1.0, 1.4) * uB.x * 2.0;
        rot = vec3(sin(a + q.x) * 40., cos(2.*a + q.x*1.1) * 60., sin(a*3. + q.x*2.) * 25.) * amt * 0.35;
        float k = 0.5 + 0.5 * n.y;
        accent = pick * step(0.6, k);
        br = 0.55 + 0.45 * k;
    } else {
        float f = l / max(L - 1., 1.);
        pos.z = -f * uC.w;
        float a = TAU * p;
        rot.y = sin(a) * 25. * (0.3 + f);
        rot.x = cos(a) * 12. * f;
        br = pow(1. - f, 1.4) * 0.85 + (l < 0.5 ? 0.15 : 0.);
        accent = pick * (l < 0.5 ? 1. : 0.);
    }
    vec4 o = vec4(0.);
    int ch = int(uD.x + 0.5);
    if(ch == 0) o = vec4(pos, 1.);
    else if(ch == 1) o = vec4(rot, 1.);
    else if(ch == 2) o = vec4(scl.x, scl.y, 1., 1.);
    else if(ch == 3) o = vec4(mix(uE.rgb * br, uF.rgb * br * 1.2, accent), 1.);
    else if(ch == 4) o = vec4(uvo, uvs);
    fragColor = o;
}
