uniform vec4 uE;   // x = exposure
uniform vec3 uBg;
out vec4 fragColor;
void main(){
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    c = 1.0 - exp(-c * uE.x);
    fragColor = TDOutputSwizzle(vec4(uBg + c * (1.0 - uBg), 1.0));
}
