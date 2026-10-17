// Default studio environment (equirectangular): dusk sky gradient, warm horizon band, softboxes, dark floor.
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    float az = (uv.x - 0.5) * 6.2831853;
    float el = (uv.y - 0.5) * 3.1415927;
    vec3 d = vec3(sin(az) * cos(el), sin(el), -cos(az) * cos(el));
    float up = d.y;
    vec3 sky = mix(vec3(0.55, 0.50, 0.46), vec3(0.10, 0.20, 0.45), smoothstep(0.0, 0.8, up));
    vec3 ground = mix(vec3(0.10, 0.09, 0.09), vec3(0.02, 0.02, 0.025), smoothstep(0.0, -0.7, up));
    vec3 c = up > 0.0 ? sky : ground;
    c += vec3(1.0, 0.55, 0.25) * exp(-pow(up / 0.07, 2.0)) * 1.2;                         // horizon glow
    c += vec3(7.0) * smoothstep(0.93, 0.95, dot(d, normalize(vec3(-0.5, 0.7, -0.5))));       // key softbox
    c += vec3(2.0, 3.0, 5.0) * smoothstep(0.96, 0.975, dot(d, normalize(vec3(0.8, 0.25, -0.3)))); // blue strip
    c += vec3(3.0, 1.5, 0.8) * smoothstep(0.97, 0.985, dot(d, normalize(vec3(0.2, 0.15, 0.9))));  // warm back light
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
