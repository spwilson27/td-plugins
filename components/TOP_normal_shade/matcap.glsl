// Default matcap (studio chrome-clay): soft key, cool rim, dark core. 512x512, sphere inscribed in the frame.
out vec4 fragColor;
void main(){
    vec2 p = vUV.st * 2.0 - 1.0;
    float rr = length(p);
    vec3 n = vec3(p, sqrt(max(0.0, 1.0 - rr * rr)));
    if (rr > 1.0) n = vec3(p / rr, 0.0);
    n = normalize(n);
    vec3 L = normalize(vec3(-0.5, 0.6, 0.65));
    float nl = dot(n, L);
    float wrap = clamp((nl + 0.5) / 1.5, 0.0, 1.0);
    float fr = pow(1.0 - clamp(n.z, 0.0, 1.0), 3.0);
    vec3 H = normalize(L + vec3(0.0, 0.0, 1.0));
    vec3 c = vec3(0.72, 0.68, 0.62) * (0.08 + 0.95 * wrap * wrap)
           + vec3(0.35, 0.5, 0.8) * fr * 0.55
           + vec3(1.0) * pow(max(dot(n, H), 0.0), 60.0) * 0.8;
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
