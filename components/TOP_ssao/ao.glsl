// TOP_ssao pass 1: raw ambient occlusion. in0 = depth (R), in1 = view-space normals.
out vec4 fragColor;
uniform vec4 uA;   // depthmode, near, far, depthscale
uniform vec4 uB;   // fov (deg), radius (world), samples, bias
uniform vec4 uC;   // normal encoding (0 signed -1..1, 1 packed 0..1)
// returns linear eye-space z, or -1 for sky / no geometry
float decodeDepth(float d){
    if (uA.x < 0.5) {
        if (d <= 0.0 || d >= uA.z * 0.999) return -1.0;
        return d * uA.w;
    }
    if (d >= 0.99999) return -1.0;
    float n = uA.y, f = uA.z;
    float z = d * 2.0 - 1.0;
    return 2.0 * n * f / (f + n - z * (f - n));
}
void main(){
    vec2 uv = vUV.st;
    float d = decodeDepth(texture(sTD2DInputs[0], uv).r);
    vec3 nrm = texture(sTD2DInputs[1], uv).rgb;
    if (uC.x > 0.5) nrm = nrm * 2.0 - 1.0;
    if (d < 0.0 || dot(nrm, nrm) < 0.01) { fragColor = vec4(1.0); return; }
    vec3 n = normalize(nrm);
    float asp = uTDOutputInfo.res.z / uTDOutputInfo.res.w;
    float th = tan(radians(max(uB.x, 1.0)) * 0.5);
    vec2 k2 = vec2(th * asp, th);
    vec3 P = vec3((uv * 2.0 - 1.0) * k2, -1.0) * d;
    float ign = fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715))));
    int N = int(uB.z + 0.5);
    float occ = 0.0;
    for (int i = 0; i < 64; i++) {
        if (i >= N) break;
        float fi = (float(i) + 0.5) / float(N);
        float cz = 1.0 - 2.0 * fi;
        float sr = sqrt(max(1.0 - cz * cz, 0.0));
        float ph = float(i) * 2.399963 + ign * 6.2831853;
        vec3 k = vec3(sr * cos(ph), sr * sin(ph), cz);
        k *= (dot(k, n) < 0.0 ? -1.0 : 1.0);
        float sc = 0.15 + 0.85 * fract(float(i) * 0.6180339 + ign);
        vec3 sp = P + (k + n * 0.15) * uB.y * sc;
        if (sp.z > -0.01) continue;
        vec2 suv = (sp.xy / (-sp.z) / k2) * 0.5 + 0.5;
        float ds = decodeDepth(texture(sTD2DInputs[0], suv).r);
        if (ds < 0.0) continue;
        float zs = -ds;
        float rng = smoothstep(0.0, 1.0, uB.y / max(abs(P.z - zs), 1e-4));
        occ += (zs >= sp.z + uB.w ? 1.0 : 0.0) * rng;
    }
    float ao = 1.0 - occ / float(N);
    fragColor = TDOutputSwizzle(vec4(vec3(ao), 1.0));
}
