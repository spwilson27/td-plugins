uniform vec4 uA; // p, spinturns, bounces, kaleido folds
uniform vec4 uB; // shape, objsize, sway, fov
uniform vec4 uC; // roomW, roomH, roomD, steps
uniform vec4 uD; // lineGlow, exposure, palette, seed
uniform vec4 uE; // custom rgb, mirror reflectivity
out vec4 fragColor;
const float TAU = 6.28318530718;
mat2 rot(float a){ float c=cos(a), s=sin(a); return mat2(c,-s,s,c); }
float h11(float n){ return fract(sin(n*127.1 + uD.w*13.7)*43758.5453); }
float sdBox(vec3 p, vec3 b){ vec3 q = abs(p)-b; return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.); }
float sdTorus(vec3 p, vec2 t){ vec2 q = vec2(length(p.xz)-t.x, p.y); return length(q)-t.y; }

float sdObj(vec3 p){
    float ph = TAU * uA.x;
    // spin about y and tumble about x (integer turns per loop => periodic)
    p.xz = rot(ph * uA.y) * p.xz;
    p.yz = rot(ph * uA.y * 0.5 + 0.6) * p.yz;
    // kaleidoscopic folds
    int nf = int(uA.w + 0.5);
    for(int i=0;i<4;i++){
        if(i >= nf) break;
        p = abs(p) - vec3(0.8, 0.5, 0.6) * uB.y;
        p.xy = rot(0.55 + 0.25*sin(ph)) * p.xy;
        p.yz = rot(0.35) * p.yz;
    }
    int sh = int(uB.x + 0.5);
    float s = uB.y / (1.0 + 0.5*float(nf));
    if(sh == 0) return length(p) - 0.9 * s;
    if(sh == 1) return sdTorus(p, vec2(0.85*s, 0.3*s));
    // twisted torus (trefoil-like knot): elliptical cross section rotating 3/2 times around the ring
    float a = atan(p.z, p.x);
    vec2 q = vec2(length(p.xz) - 0.9*s, p.y);
    q = rot(a * 1.5 + ph) * q;
    return (length(q * vec2(1.0, 1.7)) - 0.26*s) * 0.6;
}
float room(vec3 p){ return -sdBox(p, vec3(uC.xyz)); }
float map(vec3 p, out float mat){
    float dr = room(p), dobj = sdObj(p);
    if(dobj < dr){ mat = 1.0; return dobj; }
    mat = 0.0; return dr;
}
float mapd(vec3 p){ float m; return map(p, m); }
vec3 pal(int k, float t){
    if(k == 0) return vec3(0.92,0.92,0.9);
    if(k == 1) return mix(vec3(0.92,0.9,0.84), vec3(1.0,0.07,0.03), t);
    if(k == 2) return mix(vec3(0.7,0.85,1.0), vec3(0.3,0.5,1.0), t);
    return mix(uE.rgb, uE.rgb*vec3(1.0,0.2,0.2), t);
}
vec3 wallEmit(vec3 pos, vec3 n){
    vec3 H = uC.xyz;
    vec2 uv;
    float cell;
    if(abs(n.x) > 0.5){ uv = pos.zy; cell = 1.0; }
    else if(abs(n.y) > 0.5){ uv = pos.xz; cell = 2.0; }
    else { uv = pos.xy; cell = 3.0; }
    // grid lines
    vec2 g = abs(fract(uv * 0.5 + 0.25) - 0.5);
    float line = smoothstep(0.035, 0.0, min(g.x, g.y) );
    // light panels (hash per tile)
    vec2 id = floor(uv * 0.5 + 0.25);
    float r = h11(dot(id, vec2(1.0, 37.0)) + cell*11.0);
    float panel = step(0.935, r) * smoothstep(0.30, 0.22, max(g.x, g.y) * 1.0);
    float pulse = 0.6 + 0.4 * cos(TAU * (uA.x * floor(1.0 + r*2.0)) + r * TAU);
    int k = int(uD.z + 0.5);
    vec3 e = pal(k, 0.0) * line * 0.55 * uD.x + pal(k, step(0.975, r)) * panel * 2.5 * pulse * uD.x;
    return e;
}
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = (vUV.st - 0.5) * vec2(res.x/res.y, 1.0);
    float ph = TAU * uA.x;
    float tf = tan(radians(uB.w * 0.5));
    vec3 ro = vec3(sin(ph) * 0.6 * uB.z, 0.35 * cos(ph) * uB.z - 0.2, -uC.z * 0.62);
    vec3 target = vec3(0.0);
    vec3 fw = normalize(target - ro);
    vec3 rt = normalize(cross(vec3(0,1,0), fw));
    vec3 up = cross(fw, rt);
    vec3 rd = normalize(fw + (rt * uv.x + up * uv.y) * 2.0 * tf);
    vec3 col = vec3(0.0), thr = vec3(1.0);
    int nb = int(uA.z + 0.5);
    int steps = int(uC.w);
    for(int b = 0; b <= 8; b++){
        if(b > nb) break;
        float t = 0.01, mat = 0.0; bool hit = false;
        for(int i=0;i<steps;i++){
            float d = map(ro + rd*t, mat);
            if(d < 0.001) { hit = true; break; }
            t += d;
            if(t > 60.0) break;
        }
        if(!hit){ col += thr * vec3(0.02); break; }
        vec3 pos = ro + rd*t;
        vec2 e = vec2(0.002, 0.0);
        vec3 n = normalize(vec3(mapd(pos+e.xyy)-mapd(pos-e.xyy), mapd(pos+e.yxy)-mapd(pos-e.yxy), mapd(pos+e.yyx)-mapd(pos-e.yyx)));
        float fres = pow(1.0 - max(dot(-rd, n), 0.0), 4.0);
        if(mat < 0.5){
            // mirror wall: dark mirror with emissive lines
            col += thr * wallEmit(pos, n);
            thr *= uE.w * (0.85 + 0.15 * fres);
        } else {
            // chrome object
            col += thr * 0.02;
            thr *= mix(0.88, 1.0, fres) * vec3(0.95, 0.96, 1.0);
        }
        rd = reflect(rd, n);
        ro = pos + n * 0.01;
        if(max(thr.r, max(thr.g, thr.b)) < 0.01) break;
    }
    col = 1.0 - exp(-col * uD.y);
    col *= 1.0 - 0.3 * dot(uv, uv);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
