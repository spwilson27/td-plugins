// TOP_normal_shade. in0 = view-space normals, in1 = matcap, in2 = albedo colour (white if unconnected).
out vec4 fragColor;
uniform vec4 uA;   // mode (0 matcap, 1 lights), normal encoding (0 signed, 1 packed), matcap rotate (rad), matcap flip y
uniform vec4 uB;   // key azimuth (rad), key elevation (rad), key intensity, ambient
uniform vec4 uC;   // key colour rgb, fill intensity
uniform vec4 uD;   // fill colour rgb, rim intensity
uniform vec4 uE;   // rim colour rgb, rim power
uniform vec4 uF;   // spec amount, spec power, wrap, colour mix (albedo influence)
uniform vec4 uG;   // brightness, background mode (0 transparent, 1 colour input)

vec3 dirAE(float az, float el){ return normalize(vec3(sin(az) * cos(el), sin(el), cos(az) * cos(el))); }

void main(){
    vec2 uv = vUV.st;
    vec3 nr = texture(sTD2DInputs[0], uv).rgb;
    if (uA.y > 0.5) nr = nr * 2.0 - 1.0;
    vec3 alb = texture(sTD2DInputs[2], uv).rgb;
    if (dot(nr, nr) < 0.01) {
        fragColor = TDOutputSwizzle(vec4(uG.y > 0.5 ? alb : vec3(0.0), uG.y > 0.5 ? 1.0 : 0.0));
        return;
    }
    vec3 n = normalize(nr);
    vec3 c;
    if (uA.x < 0.5) {
        vec2 p = n.xy;
        if (uA.w > 0.5) p.y = -p.y;
        float cs = cos(uA.z), sn = sin(uA.z);
        p = vec2(cs * p.x - sn * p.y, sn * p.x + cs * p.y);
        c = texture(sTD2DInputs[1], p * 0.5 + 0.5).rgb;
    } else {
        vec3 v = vec3(0.0, 0.0, 1.0);
        vec3 K = dirAE(uB.x, uB.y);
        vec3 F = dirAE(uB.x + 3.14159, -uB.y * 0.3);
        float w = uF.z;
        float dk = clamp((dot(n, K) + w) / (1.0 + w), 0.0, 1.0);
        float df = clamp((dot(n, F) + w) / (1.0 + w), 0.0, 1.0);
        float rim = pow(1.0 - clamp(dot(n, v), 0.0, 1.0), max(uE.w, 0.1));
        vec3 H = normalize(K + v);
        float sp = pow(max(dot(n, H), 0.0), uF.y) * uF.x * step(0.0, dot(n, K));
        c = vec3(uB.w) + uC.rgb * dk * uB.z + uD.rgb * df * uC.w + uE.rgb * rim * uD.w + vec3(sp) * uC.rgb;
        c *= mix(vec3(1.0), alb, uF.w);
    }
    if (uA.x < 0.5) c *= mix(vec3(1.0), alb, uF.w);
    fragColor = TDOutputSwizzle(vec4(c * uG.x, 1.0));
}
