// Composite trails over the input image. in0 = trail (R), in1 = input image.
uniform vec3 uC1; uniform vec3 uC2; uniform vec3 uC3; uniform vec3 uTint;
uniform vec4 uM;   // x=colour mode (0 ramp,1 tint,2 image) y=compose (0 over,1 add,2 screen) z=input level w=gain
out vec4 fragColor;
void main(){
    float v = texture(sTD2DInputs[0], vUV.st).r;
    vec4 s4 = texture(sTD2DInputs[1], vUV.st);
    vec3 s = s4.rgb;
    float t = 1.0 - exp(-v*uM.w);
    vec3 col;
    if (uM.x < 0.5) col = t < 0.5 ? mix(uC1, uC2, t*2.0) : mix(uC2, uC3, t*2.0-1.0);
    else if (uM.x < 1.5) col = uTint;
    else { float m = max(max(s.r, s.g), max(s.b, 0.02)); col = clamp(s/m, 0.0, 1.0) * (0.6 + 0.8*t); }
    vec3 base = s * uM.z;
    vec3 r;
    if (uM.y < 0.5) r = mix(base, col, t);
    else if (uM.y < 1.5) r = base + col*t;
    else r = 1.0 - (1.0 - base)*(1.0 - col*t);
    fragColor = TDOutputSwizzle(vec4(r, 1.0));
}
