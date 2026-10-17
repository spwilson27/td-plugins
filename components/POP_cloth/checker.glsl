// Checker texture for the preview cloth. uA = colour A, uB = colour B, uC.x = cells per side
uniform vec4 uA, uB, uC;
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st * uC.x;
    float k = mod(floor(uv.x) + floor(uv.y), 2.0);
    fragColor = TDOutputSwizzle(vec4(mix(uA.rgb, uB.rgb, k), 1.0));
}
