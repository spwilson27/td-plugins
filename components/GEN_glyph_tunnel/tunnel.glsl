uniform vec4 uA; // N chars, mode(0 tunnel,1 wall,2 rain), p, cols
uniform vec4 uB; // looprows, flickersteps, fog, rollturns
uniform vec4 uC; // sway, density, accentAmt, seed
uniform vec4 uD; // tint rgb, brightness
uniform vec4 uE; // accent rgb, trail
uniform vec4 uF; // fov(deg), 0,0,0
out vec4 fragColor;
const float TAU = 6.28318530718;
float h11(float n){ return fract(sin(n*127.1 + uC.w*17.31)*43758.5453); }
float h21(vec2 p){ return h11(dot(p, vec2(1.0, 57.0))); }
mat2 rot(float a){ float c=cos(a), s=sin(a); return mat2(c,-s,s,c); }

float glyph(float g, vec2 f, float lod){
    float N = uA.x;
    vec2 uv = vec2((g + clamp(f.x,0.02,0.98)) / N, f.y);
    float v = texture(sTD2DInputs[0], uv).r;
    return mix(v, 0.28, lod);
}

void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 q = (vUV.st - 0.5) * vec2(res.x/res.y, 1.0);
    float p = uA.z;
    int mode = int(uA.y + 0.5);
    float cols = uA.w, LR = uB.x;
    float tf = tan(radians(uF.x*0.5));
    vec3 rd = normalize(vec3(q * 2.0 * tf, 1.0));
    vec3 ro = vec3(0.);
    float roll = TAU * p * uB.w;
    float sw = uC.x;
    vec2 cell; float t = -1.0; vec2 f; float colId = 0., rowId = 0.;
    float colw, cellh;
    vec2 cp;
    if(mode == 0){
        rd.xy = rot(roll) * rd.xy;
        ro.xy = vec2(cos(TAU*p), sin(2.*TAU*p)) * 0.18 * sw;
        float R = 1.0;
        float a = dot(rd.xy, rd.xy), b = dot(ro.xy, rd.xy), c = dot(ro.xy, ro.xy) - R*R;
        float disc = b*b - a*c;
        t = (-b + sqrt(max(disc, 0.))) / a;
        vec3 hp = ro + rd * t;
        float th = atan(hp.y, hp.x) / TAU + 0.5;
        colw = 1.0 / cols;
        cellh = TAU / cols;                      // cell width in world = 2pi/cols ; height = 2*width
        cellh *= 2.0;
        cp = vec2(th * cols, hp.z / cellh - p * LR);
    } else {
        // wall / rain: plane at z = 2, tilted
        float ya = sin(TAU*p) * 0.35 * sw, xa = cos(TAU*p) * 0.18 * sw;
        rd.xz = rot(ya) * rd.xz; rd.yz = rot(xa) * rd.yz;
        vec3 n = vec3(0., 0., 1.);
        t = 2.0 / rd.z;
        vec3 hp = ro + rd * t;
        // rotate hit back into plane frame
        vec2 w = hp.xy * 2.0;
        float cw = 6.0 / cols;
        cp = vec2(w.x / cw + cols*0.5, w.y / (cw*2.0));
    }
    vec2 ci = floor(cp);
    f = fract(cp);
    f.y = f.y;
    float col = mod(ci.x, cols);
    float row = mod(ci.y, LR);
    if(mode == 2){
        // rain: each column falls at integer speed (rows per loop) with its own offset
        float sp = 1.0 + floor(h11(col*3.1) * 3.0);
        float off = floor(h11(col*7.7) * LR);
        float rr = mod(cp.y + p * LR * sp * 1.0 + off, LR);   // falling coordinate (rows)
        row = floor(rr);
        f.y = fract(rr);
        float head = mod(floor(p*LR*sp) , LR);
        float dist = mod(row - (0.0), LR);
        // trail: distance behind head along the fall direction
        float tr = mod(floor(rr) , LR) / LR;      // 0..1 along period
        float bright = pow(1.0 - tr, 1.0 + uE.w * 6.0);
        ci = vec2(col, row);
        cp.y = rr;
        // reuse below as modulation
        f = vec2(f.x, f.y);
        colId = bright;
    }
    // glyph selection with periodic flicker
    float S = max(uB.y, 1.0);
    float ph = h21(vec2(col, row));
    float k = mod(floor(p * S + ph * S), S);
    float flick = step(0.5, h21(vec2(col, row) + 9.1));  // half of cells flicker
    float gid = floor(h21(vec2(col, row) + 0.5 + flick * k * 3.7) * uA.x);
    float lit = step(1.0 - uC.y, h21(vec2(col, row) + 33.3));
    float fw = max(fwidth(cp.x), fwidth(cp.y));
    float lod = smoothstep(0.25, 0.9, fw);
    float gl = glyph(gid, f, lod);
    // brightness waves (periodic): a band travelling along rows / across columns
    float wave;
    if(mode == 0) wave = pow(0.5 + 0.5*cos(TAU*(row/LR - p)), 4.0);
    else if(mode == 1) wave = pow(0.5 + 0.5*cos(TAU*((row/LR) + col/cols - p)), 3.0);
    else wave = colId;
    float br = (0.18 + 0.9 * wave) * mix(0.35, 1.0, lit);
    float fog = exp(-max(t - 1.0, 0.0) * uB.z * (mode == 0 ? 0.35 : 0.5));
    if(mode == 0) fog = exp(-max(t - 1.0, 0.0) * uB.z * 0.12);
    float accent = step(1.0 - uC.z, h21(vec2(col, row) + 71.7)) * (0.3 + 0.7*wave);
    vec3 base = mix(uD.rgb, uE.rgb, clamp(accent, 0., 1.));
    vec3 c = base * gl * br * fog * uD.w;
    // faint center vignette / depth glow in tunnel
    if(mode == 0){
        float glow = exp(-t * 0.35) * 0.0;
        c += uD.rgb * glow;
        c *= smoothstep(0., 1., fog * 4.0);
    }
    if(t < 0.0) c = vec3(0.);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
