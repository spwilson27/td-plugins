uniform vec3 uC1; uniform vec3 uC2; uniform vec3 uC3; uniform float uGain;
out vec4 fragColor;
void main(){
    float v = texture(sTD2DInputs[0], vUV.st).r;
    float t = 1.0 - exp(-v*uGain);
    vec3 c = t < 0.5 ? mix(uC1, uC2, t*2.0) : mix(uC2, uC3, t*2.0-1.0);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
