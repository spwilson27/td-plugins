uniform vec4 uA;  // wirewidth px, wirebright, fill, fresnel power
uniform vec4 uB;  // fresnel amount, scan sweeps per loop, scan scale, scan sharpness
uniform vec4 uC;  // scan strength, scanline px, scanline amount, flicker
uniform vec4 uD;  // drop amount, drop block px, ticks per loop, phase
uniform vec4 uE;  // depth near, depth far, wire mode (0 object grid,1 uv grid,2 both), transparent
uniform vec4 uF;  // object grid cells per unit, uv cells u, uv cells v, crease amount
uniform vec3 uNear; uniform vec3 uFar; uniform vec3 uScanCol;
in vec3 vWorld; in vec3 vNrm; in vec3 vObj; in vec2 vUV; in vec3 vCam;
layout(location = 0) out vec4 fragColor;

float h11(float n){ return fract(sin(n * 127.1) * 43758.5453); }
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void main(){
    float ph = fract(uD.w);
    float tick = floor(ph * max(uD.z, 1.0));

    vec3 n = normalize(vNrm);
    if (!gl_FrontFacing) n = -n;
    // ---- data dropout: blocks of fragments discarded, re-rolled each tick ----
    vec2 blk = floor(gl_FragCoord.xy / max(uD.y, 2.0));
    float hb = h21(blk + tick * 7.31);
    float rowH = h21(vec2(blk.y, tick * 3.7 + 19.0));            // whole-row bursts
    float amt = uD.x;
    if (hb < amt * 0.8 || rowH < amt * 0.25) discard;

    vec3 camPos = vCam;
    vec3 V = normalize(camPos - vWorld);
    float dist = length(camPos - vWorld);
    float dz = clamp((dist - uE.x) / max(uE.y - uE.x, 1e-3), 0.0, 1.0);
    vec3 base = mix(uNear, uFar, dz);

    // ---- wire: derivative-based grid lines, constant pixel width ----
    float dm = 1e4;
    if (uE.z < 0.5 || uE.z > 1.5) {            // object-space lattice (works on any mesh)
        vec3 f = vObj * uF.x;
        vec3 dd = abs(fract(f - 0.5) - 0.5) / max(fwidth(f), vec3(1e-6));
        dm = min(dm, min(dd.x, min(dd.y, dd.z)));
    }
    if (uE.z > 0.5) {                                            // uv iso-lines (== mesh edges on parametric shapes)
        vec2 f = vUV * uF.yz;
        vec2 dd = abs(fract(f - 0.5) - 0.5) / max(fwidth(f), vec2(1e-6));
        dm = min(dm, min(dd.x, dd.y));
    }
    float wire = 1.0 - smoothstep(uA.x - 1.0, uA.x + 0.5, dm);
    // crease edges: normal discontinuities / silhouettes
    float cr = length(fwidth(n)) * uF.w;
    wire = max(wire, clamp(cr - 0.15, 0.0, 1.0));

    // ---- fresnel rim ----
    float fr = pow(1.0 - abs(dot(n, V)), uA.w);

    // ---- scan band sweeping along world Y; loops: integer sweeps per loop ----
    float u = fract(vWorld.y * uB.z * 0.25 - ph * uB.y);
    float band = pow(1.0 - u, uB.w) * smoothstep(0.0, 0.02, u);
    float lines = 1.0 - uC.z * (0.5 + 0.5 * sin(gl_FragCoord.y * 6.2831853 / max(uC.y, 1.5)));

    float flick = 1.0 - uC.w * (h11(tick * 1.7 + 3.0) > 0.78 ? 1.0 : 0.25 * h11(tick));
    vec3 col = base * (wire * uA.y + uA.z + fr * uB.x);
    col += uScanCol * band * uC.x * (wire * 1.2 + 0.25 + fr);
    col *= lines * flick;

    float a = clamp(max(col.r, max(col.g, col.b)), 0.0, 1.0);
    if (uE.w > 0.5) fragColor = TDOutputSwizzle(vec4(col, a));
    else fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
