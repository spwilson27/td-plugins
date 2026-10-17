// Random initial velocities (unit-ish * speed). Input0 only used for its size.
out vec4 fragColor;
uniform float uSeed;
uniform float uSide;
uniform float uSpeed;
vec3 hash3(vec3 p){
    p = fract(p * vec3(.1031, .1030, .0973) + uSeed*0.0291);
    p += dot(p, p.yxz + 33.33);
    return fract((p.xxy + p.yxx) * p.zyx);
}
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    float idx = float(ip.y * int(uSide) + ip.x);
    vec3 r = hash3(vec3(idx*0.61, idx, 5.3)) * 2.0 - 1.0;
    fragColor = TDOutputSwizzle(vec4(normalize(r + 1e-4) * uSpeed, 0.0));
}
