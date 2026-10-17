// Preview-only test image: drifting soft blobs and a ring on a grey ground (gives the sim a luminance landscape).
out vec4 fragColor;
uniform float uTime;
void main(){
    vec2 uv = vUV.st;
    vec2 q = (uv - 0.5) * vec2(1.7778, 1.0);
    float v = 0.30 + 0.12*sin(q.x*3.0 + uTime*0.2);
    for (int i = 0; i < 4; i++) {
        float fi = float(i);
        vec2 c = 0.42*vec2(sin(uTime*0.23 + fi*1.9), cos(uTime*0.31 + fi*2.7));
        v += 0.55*exp(-dot(q-c, q-c)*mix(14.0, 40.0, fract(fi*0.37)));
    }
    float r = length(q - vec2(0.0, 0.0));
    v += 0.5*smoothstep(0.015, 0.0, abs(r - (0.30 + 0.05*sin(uTime*0.5))));
    vec3 col = mix(vec3(0.35,0.20,0.10), vec3(1.0,0.9,0.7), clamp(v, 0.0, 1.0));
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
