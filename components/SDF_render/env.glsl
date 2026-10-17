// built-in sky environment (equirectangular): dark ground, bright horizon, soft blue sky
out vec4 fragColor;
void main(){
    float e = vUV.y * 2.0 - 1.0;
    vec3 sky = mix(vec3(0.85, 0.82, 0.78), vec3(0.03, 0.09, 0.3), pow(clamp(e, 0.0, 1.0), 0.28));
    vec3 gnd = mix(vec3(0.35, 0.33, 0.32), vec3(0.015, 0.015, 0.02), pow(clamp(-e, 0.0, 1.0), 0.35));
    vec3 c = e > 0.0 ? sky : gnd;
    float sun = pow(max(1.0 - length(vec2((vUV.x - 0.62) * 6.0, (vUV.y - 0.68) * 9.0)), 0.0), 3.0);
    fragColor = TDOutputSwizzle(vec4(c + vec3(1.0, 0.85, 0.6) * sun * 2.0, 1.0));
}
