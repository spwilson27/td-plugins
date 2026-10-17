// SDF_to_MAT: raymarch the SDF in the object space of the proxy geometry, write color + depth
//@@SDF@@
//@@LIB@@
in vec3 vObj;
flat in int vCam;
uniform vec4 uBc;   // proxy bounds center
uniform vec4 uBs;   // proxy bounds size
uniform vec4 uA;    // steps, epsilon, step scale, gamma
uniform vec4 uB;    // shadow hardness, ao, key azimuth (rad), key elevation (rad)
layout(location = 0) out vec4 fragColor;

void main(){
    mat4 wm = uTDMats[vCam].world;
    mat4 wi = uTDMats[vCam].worldInverse;
    vec3 camW = uTDMats[vCam].camInverse[3].xyz;
    vec3 ro = (wi * vec4(camW, 1.0)).xyz;
    vec3 rd = normalize(vObj - ro);
    // ray / bounds box
    vec3 hb = 0.5 * uBs.xyz;
    vec3 inv = 1.0 / rd;
    vec3 t0v = (uBc.xyz - hb - ro) * inv, t1v = (uBc.xyz + hb - ro) * inv;
    vec3 tmn = min(t0v, t1v), tmx = max(t0v, t1v);
    float tn = max(max(tmn.x, tmn.y), max(tmn.z, 0.0)), tf = min(tmx.x, min(tmx.y, tmx.z));
    if (tf < tn) discard;
    float t; vec3 alb;
    float eps = uA.y;
    if (!sdMarch(ro, rd, tn, tf, int(uA.x), eps, uA.z, t, alb)) discard;
    vec3 p = ro + rd * t;
    vec3 n = sdNormal(p, max(eps, 0.0005));
    float el = uB.w, az = uB.z;
    vec3 lw = normalize(vec3(cos(el) * sin(az), sin(el), cos(el) * cos(az)));
    vec3 lo = normalize(mat3(wi) * lw);
    vec3 sky = sdSky(n);
    vec3 col = sdLight(p, n, rd, alb, lo, uB.x, uB.y, sky);
    col = clamp((col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14), 0.0, 1.0);
    col = pow(col, vec3(1.0 / uA.w));
    vec4 clip = uTDMats[vCam].camProj * (wm * vec4(p, 1.0));
    gl_FragDepth = clip.z / clip.w * 0.5 + 0.5;
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
