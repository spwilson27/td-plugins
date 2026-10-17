uniform vec4 uA; // p (unwrapped loop phase), nseg, seglen, variation
uniform vec4 uB; // halfW, halfH, roll amount, sway
uniform vec4 uC; // fov, fog, steps, palette
uniform vec4 uD; // exposure, ribdepth, seed, lightamt
uniform vec4 uE; // custom tint rgb, -
out vec4 fragColor;
const float TAU = 6.28318530718;
float h11(float n){ return fract(sin(n*127.1 + uD.z*13.7)*43758.5453); }
float sdRBox2(vec2 p, vec2 b, float r){ vec2 q = abs(p)-b+r; return length(max(q,0.))+min(max(q.x,q.y),0.)-r; }
float sdBox(vec3 p, vec3 b){ vec3 q = abs(p)-b; return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.); }
mat2 rot(float a){ float c=cos(a), s=sin(a); return mat2(c,-s,s,c); }

float gLd = 1e9; float gLm = 2.0;
// returns distance; mat: 0 wall, 1 rib/frame, 2 light strip, 3 accent light
float map(vec3 q, out float mat, out float segid){
    float L = uA.z;
    float s = floor(q.z / L + 0.5);
    float zl = q.z - s * L;
    float sid = mod(s, uA.y);
    segid = sid;
    float r = h11(sid);
    float u0 = h11(sid + 5.3);
    float typ = r < (1.0 - uA.w) ? 0.0 : (u0 < 0.4 ? 1.0 : (u0 < 0.85 ? 2.0 : 3.0));   // 0 plain,1 ribs,2 lights,3 door
    vec2 xy = q.xy;
    vec2 hb = uB.xy;
    float shell = -sdRBox2(xy, hb, 0.55);
    float d = shell; mat = 0.0;
    // thin ring at every segment joint (center of cell is a joint-free zone: put ring at cell centre)
    float ring = max(shell - 0.10, abs(zl) - 0.04);
    if(ring < d){ d = ring; mat = 1.0; }
    if(typ == 1.0){
        // heavy ribs: three arches
        for(int i=-1;i<=1;i++){
            float rb = max(shell - uD.y, abs(zl - float(i)*L*0.3) - 0.07);
            if(rb < d){ d = rb; mat = 1.0; }
        }
    } else if(typ == 2.0){
        float lz = L * 0.36;
        float up = sdBox(vec3(xy.x, xy.y - (hb.y - 0.03), zl), vec3(0.45, 0.05, lz));
        float dn = sdBox(vec3(xy.x, xy.y + (hb.y - 0.03), zl), vec3(0.45, 0.05, lz));
        float ls = min(up, dn);
        gLd = min(gLd, ls); gLm = (h11(sid + 9.1) < 0.3) ? 3.0 : 2.0;
        if(ls < d){ d = ls; mat = (h11(sid + 9.1) < 0.3) ? 3.0 : 2.0; }
    } else if(typ == 3.0){
        float hole = sdRBox2(xy, hb * vec2(0.55, 0.65), 0.3);
        float fr = max(abs(zl) - 0.12, -hole);
        if(fr < d){ d = fr; mat = 1.0; }
        float edge = max(abs(zl) - 0.14, abs(hole) - 0.03);
        gLd = min(gLd, edge); gLm = 3.0;
        if(edge < d){ d = edge; mat = 3.0; }
    }
    return d;
}
float mapd(vec3 q){ float m, sg; return map(q, m, sg); }

vec3 palette(float k, int pal, out vec3 acc){
    // returns wall albedo base; acc = accent light colour
    if(pal == 0){ acc = vec3(1.0, 0.1, 0.05); return vec3(0.75,0.74,0.70); }       // bone + red
    if(pal == 1){ acc = vec3(0.6, 0.8, 1.0);  return vec3(0.6,0.65,0.72); }       // chrome / ice
    if(pal == 2){ acc = vec3(1.0, 0.45, 0.1); return vec3(0.55,0.5,0.46); }       // ember
    acc = uE.rgb * 1.5; return uE.rgb;                                           // custom
}

void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = (vUV.st - 0.5) * vec2(res.x/res.y, 1.0);
    float p = uA.x;
    float L = uA.z;
    float travel = p * uA.y * L;
    vec3 ro = vec3(sin(TAU*p) * 0.25 * uB.w, cos(TAU*p) * 0.18 * uB.w, travel);
    float roll = sin(TAU * p) * uB.z;
    float tf = tan(radians(uC.x * 0.5));
    vec3 rd = normalize(vec3(uv * 2.0 * tf, 1.0));
    rd.xy = rot(roll) * rd.xy;
    rd.xz = rot(sin(TAU*p + 1.0) * 0.06 * uB.w) * rd.xz;
    float t = 0.0, mat = 0.0, sg = 0.0; float dd = 1.0;
    int steps = int(uC.z);
    int i;
    vec3 acc0; palette(0., int(uC.w+0.5), acc0);
    vec3 glow = vec3(0.);
    for(i=0;i<steps;i++){
        gLd = 1e9;
        dd = map(ro + rd*t, mat, sg);
        if(gLd < 1e8){ vec3 gc = gLm > 2.5 ? acc0 : vec3(1.0); glow += gc * dd * 0.06 * uD.w / (0.15 + gLd*gLd*3.0) * exp(-t*0.06*uC.y); }
        if(dd < 0.0015*t || t > 60.0) break;
        t += dd * 0.8;
    }
    vec3 col = vec3(0.0);
    if(t < 60.0){
        vec3 pos = ro + rd*t;
        float m2, s2; 
        map(pos, mat, sg);
        vec2 e = vec2(0.002, 0.0);
        vec3 n = normalize(vec3(mapd(pos+e.xyy)-mapd(pos-e.xyy), mapd(pos+e.yxy)-mapd(pos-e.yxy), mapd(pos+e.yyx)-mapd(pos-e.yyx)));
        vec3 acc; vec3 alb = palette(0., int(uC.w+0.5), acc);
        // panel lines on walls
        float u = abs(n.y) > 0.5 ? pos.x : pos.y;
        float zl = pos.z;
        float lines = smoothstep(0.0, 0.03, abs(fract(u*1.2)-0.5)) * smoothstep(0.0, 0.03, abs(fract(zl/L*2.0)-0.5)*L*0.5);
        float panel = mix(0.35, 1.0, lines);
        float ao = clamp(mapd(pos + n*0.35)/0.35, 0.0, 1.0) * 0.6 + clamp(mapd(pos + n*0.9)/0.9, 0.0, 1.0)*0.4;
        vec3 lp = ro + vec3(0.0, 0.3, -0.5);
        vec3 ld = lp - pos; float dl = length(ld); ld /= dl;
        float dif = max(dot(n, ld), 0.0) / (1.0 + 0.015*dl*dl);
        vec3 h = normalize(ld - rd);
        float spec = pow(max(dot(n, h), 0.0), 40.0) / (1.0 + 0.01*dl*dl);
        vec3 base = alb * panel;
        if(mat == 1.0) base = alb * 0.45;
        col = base * (0.04 + dif * 1.4) * ao + spec * 0.8 * vec3(1.0) * ao;
        // emissive segments: nearby light strips illuminate the tube (cheap: glow by segment type)
        if(mat == 2.0) col = vec3(1.0) * 4.0 * uD.w;
        if(mat == 3.0) col = acc * 4.0 * uD.w;
        // distant lights glow: mix in accent along tube proportional to light segments
        float fog = exp(-t * uC.y * 0.05);
        col *= fog;
        col += pow(float(i)/float(steps), 3.0) * 0.0;
    }
    col += glow * 0.35;
    col *= 1.0 - 0.35 * dot(uv, uv);
    col = 1.0 - exp(-col * uD.x);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
