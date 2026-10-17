uniform vec4 uT;
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st; float asp = uTDOutputInfo.res.z / uTDOutputInfo.res.w;
    vec2 p = (uv - 0.5) * vec2(asp, 1.0);
    float t = uT.x;
    vec3 col = vec3(0.02, 0.02, 0.05);
    for (int i = 0; i < 4; i++) {
        float fi = float(i);
        vec2 c = vec2(0.42 * sin(t * (0.4 + 0.13 * fi) + fi * 1.7), 0.25 * cos(t * (0.33 + 0.1 * fi) + fi * 2.3));
        float d = length(p - c);
        vec3 hue = 0.5 + 0.5 * cos(6.2831 * (fi / 4.0 + vec3(0.0, 0.33, 0.67)));
        hue = mix(hue, vec3(1.0), 0.25);
        col = mix(col, hue, smoothstep(0.17, 0.15, d));
        col = mix(col, hue * 0.9, smoothstep(0.012, 0.0, abs(d - 0.24)) * 0.9);
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
