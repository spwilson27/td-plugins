uniform vec4 uA; // mode(0 contour,1 gradient,2 luma angle,3 hue angle), inputAmt, turbulence, noiseScale
uniform vec4 uB; // noiseTime, aspect, smoothPx, rotateRad
out vec4 fragColor;
float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
float L(vec2 uv){ return luma(texture(sTD2DInputs[0], uv).rgb); }
float hueOf(vec3 c){
    float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b)), d = mx - mn;
    if(d < 1e-4) return 0.;
    float h = (mx == c.r) ? mod((c.g - c.b)/d, 6.) : (mx == c.g) ? (c.b - c.r)/d + 2. : (c.r - c.g)/d + 4.;
    return h/6.;
}
float nz(vec2 q){ return TDPerlinNoise(vec3(q, uB.x)); }
void main(){
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy * max(uB.z, 0.5);
    // noise (curl) component
    vec2 q = vec2(uv.x*uB.y, uv.y) * uA.w;
    float e = 0.02;
    float dx = nz(q + vec2(e, 0.)) - nz(q - vec2(e, 0.));
    float dy = nz(q + vec2(0., e)) - nz(q - vec2(0., e));
    vec2 vn = vec2(dy, -dx);
    vn /= max(length(vn), 1e-5);
    // image component
    vec2 vin = vec2(0.);
    int mode = int(uA.x + 0.5);
    if(mode <= 1){
        float tl = L(uv + px*vec2(-1., 1.)), t = L(uv + px*vec2(0., 1.)), tr = L(uv + px*vec2(1., 1.));
        float l = L(uv + px*vec2(-1., 0.)), r = L(uv + px*vec2(1., 0.));
        float bl = L(uv + px*vec2(-1., -1.)), b = L(uv + px*vec2(0., -1.)), br = L(uv + px*vec2(1., -1.));
        vec2 g = vec2((tr + 2.*r + br) - (tl + 2.*l + bl), (tl + 2.*t + tr) - (bl + 2.*b + br)) * 0.25;
        float mag = clamp(length(g) * uA.y * 4., 0., 1.);
        vec2 gd = g / max(length(g), 1e-6);
        vin = (mode == 0 ? vec2(gd.y, -gd.x) : gd) * mag;
    } else {
        vec3 c = texture(sTD2DInputs[0], uv).rgb;
        float a = (mode == 2 ? luma(c) : hueOf(c)) * 6.28318 * uA.y;
        vin = vec2(cos(a), sin(a));
    }
    vec2 v = vin + vn * uA.z;
    float lv = length(v);
    vec2 d = lv > 1e-4 ? v / lv : vn;
    float cr = cos(uB.w), sr = sin(uB.w);
    d = vec2(cr*d.x - sr*d.y, sr*d.x + cr*d.y);
    fragColor = TDOutputSwizzle(vec4(d*0.5 + 0.5, clamp(lv, 0., 1.), 1.));
}
