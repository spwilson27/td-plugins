// in0 = dye. Tone-mapped colour over background.
out vec4 fragColor;
uniform float uExposure, uSat;
uniform vec3 uBg;
void main(){
    vec3 d = max(texture(sTD2DInputs[0], vUV.st).rgb, 0.0);
    float l = dot(d, vec3(0.299,0.587,0.114));
    d = mix(vec3(l), d, uSat);
    vec3 c = uBg + (1.0 - exp(-d*uExposure));
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
