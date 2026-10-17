// Boids steering (brute force over all N). in0 = positions (rgb), in1 = velocities (rgb).
out vec4 fragColor;
uniform float uCount;
uniform float uDt;           // 0 when paused
uniform float uSepW, uAliW, uCohW;
uniform float uSepR, uAliR, uCohR;
uniform float uMaxSpeed, uMinSpeed, uMaxForce;
uniform float uBound;        // half extent of the box
uniform float uWrap;         // 1 wrap, 0 bounce
uniform float uObsOn, uObsR;
uniform vec3  uObsPos;
uniform float uWander;
uniform float uTime;   // wander clock (seconds * rate)

vec3 hash3(vec3 p){
    p = fract(p * vec3(.1031, .1030, .0973));
    p += dot(p, p.yxz + 33.33);
    return fract((p.xxy + p.yxx) * p.zyx);
}

void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    ivec2 sz = textureSize(sTD2DInputs[0], 0);
    int me = ip.y * sz.x + ip.x;
    vec3 v = texelFetch(sTD2DInputs[1], ip, 0).xyz;
    if (float(me) >= uCount) { fragColor = TDOutputSwizzle(vec4(0.0)); return; }
    vec3 p = texelFetch(sTD2DInputs[0], ip, 0).xyz;

    float R2max = max(uSepR, max(uAliR, uCohR)); R2max *= R2max;
    float sr2 = uSepR*uSepR, ar2 = uAliR*uAliR, cr2 = uCohR*uCohR;
    vec3 sep = vec3(0), ali = vec3(0), coh = vec3(0);
    float na = 0.0, nc = 0.0;
    float L = 2.0*uBound;
    int N = int(uCount);
    for (int j = 0; j < N; j++) {
        if (j == me) continue;
        ivec2 jp = ivec2(j % sz.x, j / sz.x);
        vec3 q = texelFetch(sTD2DInputs[0], jp, 0).xyz;
        vec3 d = q - p;
        if (uWrap > 0.5) d -= L * round(d / L);       // nearest periodic image
        float d2 = dot(d, d);
        if (d2 > R2max || d2 < 1e-10) continue;
        if (d2 < sr2) sep -= d / d2;                 // push away, stronger when closer
        if (d2 < ar2) { ali += texelFetch(sTD2DInputs[1], jp, 0).xyz; na += 1.0; }
        if (d2 < cr2) { coh += d; nc += 1.0; }
    }
    vec3 acc = uSepW * sep * 0.3;
    if (na > 0.0) acc += uAliW * (ali / na - v);
    if (nc > 0.0) acc += uCohW * (coh / nc);
    // gentle wander so flocks keep turning
    vec3 w = hash3(vec3(float(me), floor(uTime), 3.1)) * 2.0 - 1.0;
    vec3 w2 = hash3(vec3(float(me), floor(uTime)+1.0, 3.1)) * 2.0 - 1.0;
    acc += uWander * mix(w, w2, smoothstep(0.0, 1.0, fract(uTime)));

    // obstacle (sphere) avoidance
    if (uObsOn > 0.5) {
        vec3 od = p - uObsPos;
        float dist = length(od);
        float rr = uObsR + 0.6;
        if (dist < rr) {
            vec3 n = od / max(dist, 1e-4);
            acc += n * uMaxForce * (1.0 - (dist - uObsR) / 0.6);
            if (dist < uObsR + 0.05 && dot(v, n) < 0.0) v -= 2.0 * dot(v, n) * n;
        }
    }
    // bounds
    if (uWrap < 0.5) {
        vec3 over = abs(p) - vec3(uBound);
        vec3 s = sign(p);
        // reflect when moving outward past walls, plus soft push back
        if (over.x > -0.001 && v.x*s.x > 0.0) v.x = -v.x;
        if (over.y > -0.001 && v.y*s.y > 0.0) v.y = -v.y;
        if (over.z > -0.001 && v.z*s.z > 0.0) v.z = -v.z;
        acc -= s * max(over + 0.6, 0.0) * 2.0;
    }
    float al = length(acc);
    if (al > uMaxForce) acc *= uMaxForce / al;
    v += acc * uDt;
    float sp = length(v);
    if (sp > 1e-5) v *= clamp(sp, uMinSpeed, uMaxSpeed) / sp; else v = vec3(uMinSpeed, 0, 0);
    fragColor = TDOutputSwizzle(vec4(v, 0.0));
}
