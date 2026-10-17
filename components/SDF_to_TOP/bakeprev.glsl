// raymarch the baked 3D distance texture (what SDF_to_TOP produced)
uniform vec4 uBc;
uniform vec4 uBs;
uniform vec4 uPv;
vec4 sdScene(vec3 p){
    vec3 u = (p - uBc.xyz) / uBs.xyz + 0.5;
    vec3 q = clamp(u, 0.0, 1.0);
    vec4 s = texture(sTD3DInputs[0], q);
    s.x += length((u - q) * uBs.xyz);
    return s;
}
//@@LIB@@
out vec4 fragColor;
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = (vUV.st * 2.0 - 1.0) * vec2(res.x / res.y, 1.0);
    float a = uPv.x * 0.45;
    float R = max(uBs.x, max(uBs.y, uBs.z)) * 1.15;
    vec3 ro = uBc.xyz + vec3(sin(a) * R, R * 0.5, cos(a) * R);
    vec3 fw = normalize(uBc.xyz - ro), rt = normalize(cross(fw, vec3(0, 1, 0))), up = cross(rt, fw);
    vec3 rd = normalize(fw * 1.6 + rt * uv.x + up * uv.y);
    vec3 sky = sdSky(rd);
    vec3 col = sky * 0.7;
    float t; vec3 alb;
    float e = R * 0.0015;
    if (sdMarch(ro, rd, 0.1, R * 4.0, 96, e, 0.9, t, alb)){
        vec3 p = ro + rd * t;
        vec3 n = sdNormal(p, e * 2.0);
        col = sdLight(p, n, rd, alb, normalize(vec3(0.6, 0.8, 0.5)), 0.0, 0.0, sky);
    }
    col = pow(col, vec3(0.4545));
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
