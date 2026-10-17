// frame accumulation: out = mix(current, previous, shutter). in0 prev, in1 current. uA: shutter, active, 0,0
uniform vec4 uA;
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec4 prev = texture(sTD2DInputs[0], uv);
    vec4 cur = texture(sTD2DInputs[1], uv);
    float k = uA.x * uA.y;
    fragColor = TDOutputSwizzle(mix(cur, prev, k));
}
