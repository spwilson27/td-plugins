// preview-only demo picture: drifting shaded blobs and bars so glyph colours and lum ramp are visible
uniform vec4 uT;
out vec4 fragColor;
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = (vUV.st - 0.5) * vec2(res.x / res.y, 1.0);
    float t = uT.x;
    vec3 c = mix(vec3(0.08, 0.1, 0.2), vec3(0.45, 0.6, 0.85), vUV.t);
    for(int i = 0; i < 3; i++){
        float fi = float(i);
        vec2 q = p - vec2(0.45 * sin(t * 0.4 + fi * 2.1), 0.2 * cos(t * 0.5 + fi * 1.7));
        float d = length(q);
        float r = 0.2 + 0.05 * fi;
        float s = smoothstep(r, r - 0.01, d);
        vec3 n = normalize(vec3(q, sqrt(max(r * r - d * d, 0.001))));
        float dif = clamp(dot(n, normalize(vec3(-0.4, 0.6, 0.7))), 0.0, 1.0);
        vec3 base = 0.5 + 0.5 * cos(vec3(0.0, 2.1, 4.2) + fi * 1.9 + 1.0);
        c = mix(c, base * (0.15 + dif), s);
    }
    c += 0.25 * smoothstep(0.02, 0.0, abs(p.y + 0.3 + 0.05 * sin(p.x * 6.0 + t))) * vec3(1.0, 0.8, 0.5);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
