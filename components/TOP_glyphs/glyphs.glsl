// Glyph rendering of the input image. Inputs: 0 = source image, 1 = glyph atlas (N glyphs side by side, dark->bright).
uniform vec4 uA; // N glyphs, lay (0 grid, 1 rain, 2 tunnel), cols, scroll (time*speed)
uniform vec4 uB; // contrast, invert, brightness, background
uniform vec4 uC; // tail, trailfloor, twist, seed
uniform vec4 uD; // look (0 original, 1 mono), accent, outmode (0 image, 1 index field), beat flash
out vec4 fragColor;
const float TAU = 6.28318530718;
float h11(float n){ return fract(sin(n * 127.1 + uC.w * 17.31) * 43758.5453); }
float h21(vec2 p){ return h11(dot(p, vec2(1.0, 57.0))); }
float lum(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }

vec3 cellColor(vec2 uv, vec2 spread){
    vec3 s = texture(sTD2DInputs[0], uv).rgb;
    s += texture(sTD2DInputs[0], uv + vec2( spread.x, spread.y)).rgb;
    s += texture(sTD2DInputs[0], uv + vec2(-spread.x, spread.y)).rgb;
    s += texture(sTD2DInputs[0], uv + vec2( spread.x,-spread.y)).rgb;
    s += texture(sTD2DInputs[0], uv + vec2(-spread.x,-spread.y)).rgb;
    return s * 0.2;
}

void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = vUV.st;
    float aspect = res.x / res.y;
    float N = uA.x;
    int lay = int(uA.y + 0.5);
    float cols = uA.z, t = uA.w;
    vec2 f;           // position inside the cell, (0,0) bottom-left of the glyph
    vec2 ci;          // integer cell
    vec2 suv;         // where the cell colour is sampled (uv)
    vec2 spread;      // sampling spread in uv
    float shade = 1.0; // depth / trail shading
    float head = 0.0;
    float rows = cols * res.y / (2.0 * res.x);
    if(lay == 2){
        // tunnel: polar remap of the glyph grid (cells = angle x depth)
        vec2 p = (uv - 0.5) * vec2(aspect, 1.0);
        float r = max(length(p), 1e-4);
        float a = atan(p.y, p.x) / TAU;
        const float K = 0.2;
        float Ry = 0.35 * cols / (4.0 * 3.14159265 * K);
        float zc = K / r + t * 0.35;
        float acoord = a + uC.z * zc;
        float cx = acoord * cols, cy = zc * Ry;
        ci = vec2(floor(cx), floor(cy));
        f = vec2(fract(cx), 1.0 - fract(cy));
        float zcen = (ci.y + 0.5) / Ry;
        float rc = clamp(K / max(zcen - t * 0.35, 0.02), 0.01, 1.5);
        float ac = ((ci.x + 0.5) / cols - uC.z * zcen) * TAU;
        suv = 0.5 + vec2(cos(ac), sin(ac)) * rc / vec2(aspect, 1.0);
        spread = vec2(0.006);
        shade = smoothstep(0.03, 0.2, r);
        ci.x = mod(ci.x, cols);
    } else {
        float cx = uv.x * cols, cy = (1.0 - uv.y) * rows;
        ci = floor(vec2(cx, cy));
        f = vec2(fract(cx), 1.0 - fract(cy));
        suv = vec2((ci.x + 0.5) / cols, 1.0 - (ci.y + 0.5) / rows);
        spread = vec2(0.25 / cols, 0.25 / rows);
    }
    vec3 col = cellColor(clamp(suv, 0.0, 1.0), spread);
    float L = lum(col);
    float v = clamp((L - 0.5) * uB.x + 0.5, 0.0, 1.0);
    v = mix(v, 1.0 - v, uB.y);
    float idxf = floor(v * (N - 1.0) + 0.5);
    float cell = h21(ci);
    if(lay == 1){
        float len = rows + uC.x * 3.0;
        float sp = 0.35 + h11(ci.x * 3.1) * 0.9;
        float hd = mod(t * sp * rows * 0.5 + h11(ci.x * 7.7) * len, len);
        float d = mod(hd - ci.y - 0.5, len);
        float trail = d < uC.x * 4.0 ? exp(-d / max(uC.x, 0.5)) : 0.0;
        shade = uC.y + (1.0 - uC.y) * trail;
        head = step(d, 1.0);
        if(d < 2.0) idxf = floor(h21(ci + floor(t * 12.0)) * N);
    }
    float g = 0.0;
    {
        vec2 au = vec2((idxf + clamp(f.x, 0.03, 0.97)) / N, clamp(f.y, 0.0, 1.0));
        g = texture(sTD2DInputs[1], au).r;
    }
    if(uD.z > 0.5){
        fragColor = TDOutputSwizzle(vec4(idxf / max(N - 1.0, 1.0), v, cell, 1.0));
        return;
    }
    vec3 tint;
    if(uD.x > 0.5){
        tint = vec3(0.93, 0.92, 0.88) * (0.55 + 0.45 * L);
        float acc = step(1.0 - uD.y * 0.25, cell) * step(0.25, v);
        tint = mix(tint, vec3(0.95, 0.04, 0.03), acc * step(0.001, uD.y));
    } else {
        tint = col / max(max(col.r, max(col.g, col.b)), 0.05);
    }
    vec3 bg = (uD.x > 0.5 ? vec3(L) : col) * uB.w * shade;
    vec3 c = bg + tint * g * uB.z * shade * (0.25 + 0.75 * v + 0.5 * uD.w);
    c += head * g * vec3(1.0);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
