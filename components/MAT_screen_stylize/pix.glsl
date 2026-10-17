uniform vec4 uA;   // mode (0 bayer, 1 halftone, 2 ascii), cell px, contrast, invert
uniform vec4 uB;   // halftone angle (rad), bayer levels, glyph count, ambient
uniform vec4 uC;   // light dir xyz, rim
uniform vec3 uCol1; uniform vec3 uCol2;
uniform sampler2D uAtlas;
in vec3 vWorld; in vec3 vNrm; in vec3 vCam;
layout(location = 0) out vec4 fragColor;

float m2(int x, int y){ return (x == y) ? float(x) : (x == 1 ? 2.0 : 3.0); }
float bayer8(ivec2 p){
    float v = 0.0;
    for (int i = 0; i < 3; i++) {
        int xb = (p.x >> i) & 1, yb = (p.y >> i) & 1;
        v += m2(xb, yb) * pow(4.0, float(2 - i));
    }
    return (v + 0.5) / 64.0;
}

void main(){
    vec3 n = normalize(vNrm);
    if (!gl_FrontFacing) n = -n;
    vec3 V = normalize(vCam - vWorld);
    vec3 L = normalize(uC.xyz);
    float diff = max(dot(n, L), 0.0);
    float rim = pow(1.0 - max(dot(n, V), 0.0), 3.0) * uC.w;
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(n, H), 0.0), 40.0) * 0.35;
    float lum = uB.w + (1.0 - uB.w) * diff + rim + spec;
    lum = clamp((lum - 0.5) * uA.z + 0.5, 0.0, 1.0);
    if (uA.w > 0.5) lum = 1.0 - lum;

    vec2 fc = gl_FragCoord.xy;
    float cell = max(uA.y, 1.0);
    int mode = int(uA.x + 0.5);
    float t = 0.0;

    if (mode == 0) {
        float levels = max(uB.y, 2.0);
        ivec2 ip = ivec2(floor(fc / cell));
        float b = bayer8(ip);
        t = floor(lum * (levels - 1.0) + b) / (levels - 1.0);
    } else if (mode == 1) {
        float ca = cos(uB.x), sa = sin(uB.x);
        mat2 R = mat2(ca, -sa, sa, ca);                 // screen -> grid
        vec2 g = (R * fc) / cell;
        vec2 gc = floor(g) + 0.5;
        vec2 fcCenter = transpose(R) * (gc * cell);    // cell centre back in screen px
        vec2 off = fcCenter - fc;
        float lc = clamp(lum + dFdx(lum) * off.x + dFdy(lum) * off.y, 0.0, 1.0);   // luminance at cell centre
        float r = 0.62 * sqrt(lc);
        float d = length(g - gc);
        float aa = 0.75 / cell;
        t = 1.0 - smoothstep(r - aa, r + aa, d);
    } else {
        vec2 csz = vec2(cell * 0.5, cell);
        vec2 g = fc / csz;
        vec2 gc = floor(g) + 0.5;
        vec2 fl = fract(g);
        vec2 off = (gc - g) * csz;
        float lc = clamp(lum + dFdx(lum) * off.x + dFdy(lum) * off.y, 0.0, 1.0);
        float cnt = max(uB.z, 2.0);
        float idx = floor(clamp(lc, 0.0, 0.9999) * cnt);
        vec2 auv = vec2((idx + fl.x) / 16.0, fl.y);
        t = smoothstep(0.05, 0.55, texture(uAtlas, auv).r);
    }
    vec3 col = mix(uCol1, uCol2, t);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
