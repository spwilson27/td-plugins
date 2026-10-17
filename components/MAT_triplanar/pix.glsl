uniform vec4 uA;   // scale, sharpness, pattern (0 noise,1 voronoi,2 stripes,3 grid,4 checker,5 texture), space (0 obj,1 world)
uniform vec4 uB;   // roughness, metallic, contrast, bump
uniform vec4 uC;   // animate radius, scroll cycles/loop, phase, line width
uniform vec4 uD;   // noise octaves, texture scale, 0, 0
uniform vec3 uCol1; uniform vec3 uCol2;
uniform sampler2D uTex;
in vec3 vWorld; in vec3 vNrmW; in vec3 vObj; in vec3 vNrmO; in vec3 vCam;
layout(location = 0) out vec4 fragColor;

const float TAU = 6.2831853;
vec2 h22(vec2 p){
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p){
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p, int oct){
    float a = 0.5, s = 0.0;
    mat2 R = mat2(0.8, -0.6, 0.6, 0.8) * 2.03;
    for (int i = 0; i < 8; i++) { if (i >= oct) break; s += a * vnoise(p); p = R * p; a *= 0.5; }
    return s / (1.0 - pow(0.5, float(oct)));
}
float voronoi(vec2 p, float turn){
    vec2 ip = floor(p), fp = fract(p);
    float d1 = 8.0;
    for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(i, j);
        vec2 o = h22(ip + g);
        o = 0.5 + 0.45 * sin(TAU * (turn + o));      // periodic in 'turn' (integer cycles loop)
        d1 = min(d1, length(g + o - fp));
    }
    return clamp(d1, 0.0, 1.0);
}

// returns pattern value in rgb-agnostic form: x = value 0..1, plus colour for texture in rgb of out param
float pattern(vec2 p, out vec3 texcol){
    int pat = int(uA.z + 0.5);
    float turn = uC.z;                 // phase turns
    float v = 0.0;
    texcol = vec3(0.0);
    p += vec2(17.31, 9.77) + 2.0 * uC.y * turn;            // scroll: integer cycles per loop => period-2 patterns loop
    if (pat == 0) {
        vec2 q = p + uC.x * vec2(cos(TAU * turn), sin(TAU * turn));
        v = fbm(q, int(uD.x));
    } else if (pat == 1) {
        v = voronoi(p, uC.x > 0.0 ? turn * 1.0 : 0.0);
        v = 1.0 - v;
    } else if (pat == 2) {
        float s = abs(fract(p.x) - 0.5) * 2.0;
        float aa = fwidth(p.x) * 1.5;
        v = smoothstep(uC.w - aa, uC.w + aa, s);
    } else if (pat == 3) {
        vec2 s = abs(fract(p) - 0.5) * 2.0;
        vec2 aa = fwidth(p) * 1.5;
        vec2 l = smoothstep(vec2(1.0 - uC.w) - aa, vec2(1.0 - uC.w) + aa, s);
        v = max(l.x, l.y);
    } else if (pat == 4) {
        vec2 q = floor(p);
        v = mod(q.x + q.y, 2.0);
    } else {
        texcol = texture(uTex, p * uD.y).rgb;
        v = dot(texcol, vec3(0.299, 0.587, 0.114));
    }
    return v;
}

vec3 env(vec3 r, float rough){
    float sharp = (1.0 - rough) * (1.0 - rough);
    vec3 c = mix(vec3(0.03, 0.03, 0.035), vec3(0.45, 0.48, 0.55), smoothstep(-0.1, 0.9, r.y));
    c += vec3(3.5) * smoothstep(0.88, 0.93, dot(r, normalize(vec3(-0.5, 0.7, 0.5)))) * sharp;
    c += vec3(1.5, 1.6, 1.9) * smoothstep(0.93, 0.96, dot(r, normalize(vec3(0.85, 0.2, 0.4)))) * sharp;
    return c;
}

void main(){
    bool world = uA.w > 0.5;
    vec3 P3 = (world ? vWorld : vObj) * uA.x;
    vec3 n = normalize(world ? vNrmW : vNrmO);
    vec3 nw = normalize(vNrmW);

    vec3 w = pow(abs(n), vec3(uA.y));
    w /= (w.x + w.y + w.z + 1e-6);

    vec3 tx, ty, tz;
    float vx = pattern(P3.zy, tx);
    float vy = pattern(P3.xz, ty);
    float vz = pattern(P3.xy, tz);
    float v = vx * w.x + vy * w.y + vz * w.z;
    vec3 texc = tx * w.x + ty * w.y + tz * w.z;

    v = clamp((v - 0.5) * uB.z + 0.5, 0.0, 1.0);
    vec3 albedo = (int(uA.z + 0.5) == 5) ? texc : mix(uCol1, uCol2, v);

    // derivative bump on the world normal
    vec3 N0 = normalize(vNrmW);
    if (!gl_FrontFacing) N0 = -N0;
    vec3 dpx = dFdx(vWorld), dpy = dFdy(vWorld);
    float dhx = dFdx(v), dhy = dFdy(v);
    vec3 r1 = cross(dpy, N0), r2 = cross(N0, dpx);
    float det = dot(dpx, r1);
    vec3 grad = sign(det) * (dhx * r1 + dhy * r2);
    vec3 Nb = normalize(abs(det) * N0 - uB.w * 0.02 * grad * 40.0);
    Nb = normalize(mix(N0, Nb, clamp(uB.w, 0.0, 1.0)));

    vec3 V = normalize(vCam - vWorld);
    float rough = clamp(uB.x, 0.04, 1.0);
    float metal = uB.y;
    vec3 F0 = mix(vec3(0.04), albedo, metal);
    vec3 diffc = albedo * (1.0 - metal);
    float a2 = pow(rough, 4.0);
    float expo = clamp(2.0 / a2 - 2.0, 1.0, 4000.0);
    float norm = (expo + 2.0) / 8.0 / 3.14159;

    vec3 Ls[3] = vec3[3](normalize(vec3(-0.4, 0.8, 0.5)), normalize(vec3(0.8, 0.1, 0.3)), normalize(vec3(0.0, 0.3, -1.0)));
    vec3 Lc[3] = vec3[3](vec3(3.0, 2.9, 2.8), vec3(0.6, 0.7, 0.9), vec3(1.4, 1.4, 1.5));
    vec3 col = diffc * mix(vec3(0.03, 0.03, 0.04), vec3(0.22, 0.24, 0.30), Nb.y * 0.5 + 0.5);
    float fres = pow(1.0 - max(dot(Nb, V), 0.0), 5.0);
    vec3 F = F0 + (1.0 - F0) * fres;
    for (int i = 0; i < 3; i++) {
        vec3 H = normalize(Ls[i] + V);
        float nl = max(dot(Nb, Ls[i]), 0.0);
        col += (diffc / 3.14159 * 3.0 + F * norm * pow(max(dot(Nb, H), 0.0), expo)) * Lc[i] * nl;
    }
    col += F * env(reflect(-V, Nb), rough) * (1.0 - rough * 0.6);
    col = 1.0 - exp(-col * 1.1);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
