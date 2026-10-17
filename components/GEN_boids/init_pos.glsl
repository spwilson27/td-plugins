// Random positions in the bounds box. Output rgb = position, a = 1.
out vec4 fragColor;
uniform float uBound;
uniform float uSeed;
uniform float uSide;
vec3 hash3(vec3 p){
    p = fract(p * vec3(.1031, .1030, .0973) + uSeed*0.0137);
    p += dot(p, p.yxz + 33.33);
    return fract((p.xxy + p.yxx) * p.zyx);
}
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    float idx = float(ip.y * int(uSide) + ip.x);
    vec3 r = hash3(vec3(idx, idx*0.37, 1.7));
    fragColor = TDOutputSwizzle(vec4((r*2.0-1.0)*uBound*0.9, 1.0));
}
