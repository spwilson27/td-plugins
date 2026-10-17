// TOP_depth_fog: distance / height fog + horizon glow from a depth map.
// in0 = colour, in1 = depth (R). Depth encodings: see README (linear eye-space z, or Render-TOP nonlinear + Near/Far).
out vec4 fragColor;
uniform vec4 uA;   // depthmode (0 linear, 1 nonlinear), near, far, depthscale
uniform float uCurve[128];   // fog amount f(t) for t = 0..Far, built by the native CHOP network `fog_curve` (exp / exp2 / linear)
uniform vec4 uC;   // fog colour rgb, fog amount (max opacity)
uniform vec4 uD;   // fov (deg), camera height, camera pitch (deg, + = looking down), sky blend
uniform vec4 uE;   // height fog on, base height, falloff, height density
uniform vec4 uF;   // glow amount, glow width (sin of elevation), -, -
uniform vec4 uG;   // glow colour rgb

// returns linear eye-space z distance, or -1 for sky / no geometry
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
    vec4 col = texture(sTD2DInputs[0], uv);
    float d = decodeDepth(texture(sTD2DInputs[1], uv).r);
    bool sky = d < 0.0;

    float asp = uTDOutputInfo.res.z / uTDOutputInfo.res.w;
    float th = tan(radians(max(uD.x, 1.0)) * 0.5);
    vec3 r = vec3((uv.x * 2.0 - 1.0) * th * asp, (uv.y * 2.0 - 1.0) * th, -1.0);
    float rl = length(r);
    vec3 rd = r / rl;
    float cp = cos(radians(uD.z)), sp = sin(radians(uD.z));
    float ryw = cp * rd.y + sp * rd.z;               // world-space y of the view ray
    float t = sky ? uA.z : d * rl;                    // distance along the ray

    // distance fog: read the curve (linear interpolation between its 128 samples)
    float ci = clamp(t / uA.z, 0.0, 1.0) * 127.0;
    int c0 = int(floor(ci));
    float f = mix(uCurve[c0], uCurve[min(c0 + 1, 127)], ci - float(c0));

    if (uE.x > 0.5) {
        float k = max(uE.z, 1e-4);
        float h0 = uD.y - uE.y;
        float ky = k * ryw;
        float integ = exp(-k * h0) * (abs(ky) < 1e-4 ? t : (1.0 - exp(-ky * t)) / ky);
        float fh = 1.0 - exp(-uE.w * max(integ, 0.0));
        f = 1.0 - (1.0 - f) * (1.0 - fh);
    }

    float g = uF.x * exp(-pow(abs(ryw) / max(uF.y, 1e-3), 2.0));
    vec3 fc = uC.rgb + uG.rgb * g;
    vec3 rgb;
    if (sky) rgb = mix(col.rgb, fc, uD.w);
    else     rgb = mix(col.rgb, fc, clamp(f, 0.0, 1.0) * uC.w);
    fragColor = TDOutputSwizzle(vec4(rgb, col.a));
}
