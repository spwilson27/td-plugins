// TOP_ssao: blurred AO -> applied AO mask (power + intensity). in0 = AO.
out vec4 fragColor;
uniform vec4 uA;   // intensity, power
void main(){
    float ao = texture(sTD2DInputs[0], vUV.st).r;
    ao = pow(clamp(ao, 0.0, 1.0), uA.y);
    float m = clamp(1.0 - uA.x * (1.0 - ao), 0.0, 1.0);
    fragColor = TDOutputSwizzle(vec4(vec3(m), 1.0));
}
