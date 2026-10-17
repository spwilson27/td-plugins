uniform vec4 uA; // exposure
uniform vec3 uBg;
out vec4 fragColor;
void main(){
    vec3 acc = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 c = 1. - exp(-acc*uA.x);
    fragColor = TDOutputSwizzle(vec4(uBg + c*(1.-uBg), 1.));
}
