uniform vec4 uA; // p (unwrapped loop phase), zoomPeriodsPerLoop (int, sign = direction), twist (turns per period), spin (turns per loop, int)
uniform vec4 uB; // innerScale, fill, center xy
uniform vec4 uC; // mix with original (0..1), fade, -, -
out vec4 fragColor;
const float TAU = 6.28318530718;
mat2 rot(float a){ float c=cos(a), s=sin(a); return mat2(c,-s,s,c); }
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    float asp = res.x/res.y;
    vec2 q = (vUV.st - vec2(0.5) - uB.zw) * vec2(asp, 1.0);
    q = rot(TAU * uA.w * uA.x) * q;                   // global spin: integer turns per loop
    float s = clamp(uB.x, 0.02, 0.95);
    float L = -log(s);                                 // log-scale period
    float beta = uA.z * TAU;                           // rotation gained per period (spiral)
    float R = 0.5 * uB.y;                              // image radius used (0.5 = inscribed circle)
    float r = length(q);
    float x = log(max(r, 1e-6));
    float delta = -uA.y * uA.x * L;                    // zoom: whole pattern shifts by an integer number of periods per loop
    float xs = x - delta;
    float x0 = log(R * s);
    float n = floor((xs - x0) / L);
    float ang = -(delta / L) * beta - n * beta;
    vec2 qq = rot(ang) * q * exp(-delta - n * L);
    vec2 uv = qq / vec2(asp, 1.0) + vec2(0.5);
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    // soften ring seams a little
    float f = (xs - x0) / L - n;
    float seam = smoothstep(0.0, 0.015, f) * smoothstep(0.0, 0.015, 1.0 - f);
    c *= mix(1.0, seam, uC.y);
    // fade the vanishing point
    c *= smoothstep(0.0, 0.004, r);
    vec3 o = texture(sTD2DInputs[0], vUV.st).rgb;
    fragColor = TDOutputSwizzle(vec4(mix(c, o, uC.x), 1.0));
}
