// TOP_ssao pass 2/3: depth-aware separable blur. in0 = AO, in1 = depth.
out vec4 fragColor;
uniform vec4 uA;   // depthmode, near, far, depthscale
uniform vec4 uB;   // direction x, y, radius (px), 0
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
    float dc = decodeDepth(texture(sTD2DInputs[1], uv).r);
    float c0 = texture(sTD2DInputs[0], uv).r;
    int R = int(uB.z + 0.5);
    if (R < 1 || dc < 0.0) { fragColor = vec4(vec3(c0), 1.0); return; }
    vec2 px = uTDOutputInfo.res.xy * uB.xy;
    float sum = c0, wsum = 1.0;
    float sig = max(float(R) * 0.5, 0.5);
    for (int i = 1; i <= 16; i++) {
        if (i > R) break;
        for (int s = -1; s <= 1; s += 2) {
            vec2 u2 = uv + px * float(i * s);
            float ds = decodeDepth(texture(sTD2DInputs[1], u2).r);
            if (ds < 0.0) continue;
            float w = exp(-float(i * i) / (2.0 * sig * sig)) * exp(-abs(ds - dc) / (0.04 * dc + 1e-3) );
            sum += texture(sTD2DInputs[0], u2).r * w; wsum += w;
        }
    }
    fragColor = TDOutputSwizzle(vec4(vec3(sum / wsum), 1.0));
}
