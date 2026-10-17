uniform vec4 uA; // time, count, mode, delaunay
uniform vec4 uB; // borderwidth(px), jitter, motion, seed
uniform vec4 uC; // palette, hue, glow, linewidth(px)
uniform vec4 uD; // isPhase, look(1=mono), accent, -
float fq(float f){ return uD.x > 0.5 ? max(1., floor(f + 0.5)) : f; } // integer harmonics in phase mode -> seamless loop
float hash11(float n){ return fract(sin(n*127.1+311.7)*43758.5453); }
vec2 hash21(float n){ return vec2(hash11(n), hash11(n+17.31)); }
vec2 seedPos(int i, float aspect){
    float fi = float(i);
    float N = max(uA.y, 1.);
    vec2 r = hash21(fi + uB.w*13.7);
    float gx = ceil(sqrt(N*aspect)); float gy = ceil(N/gx);
    vec2 g = (vec2(mod(fi, gx), floor(fi/gx)) + 0.5) / vec2(gx, gy);
    vec2 b = mix(g, r, uB.y);
    float t = uA.x;
    vec2 h = hash21(fi*3.7 + 5.);
    vec2 o = vec2(sin(t*fq(0.4+h.x) + h.y*6.283) + 0.5*sin(t*fq((1.1+h.y)*1.7) + h.x*9.),
                  cos(t*fq(0.35+h.y) + h.x*6.283) + 0.5*sin(t*fq((0.9+h.x)*1.9) + h.y*7.));
    b += o * 0.07 * uB.z;
    return vec2(b.x*aspect, b.y);
}
