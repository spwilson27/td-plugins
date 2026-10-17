uniform vec4 uCol0; uniform vec4 uCol1; uniform vec4 uCol2; uniform vec4 uCol3; // dead, alive(young), old, aux
uniform vec4 uM;   // x=rule y=color mode (0 flat,1 age) z=age range w=ghost amount
out vec4 fragColor;
void main(){
    vec4 c = texture(sTD2DInputs[0], vUV.st);
    int rule = int(uM.x + 0.5);
    float s = c.r;
    float t = uM.y > 0.5 ? clamp(c.g / max(uM.z, 1.0), 0.0, 1.0) : 0.0;
    vec3 col = uCol0.rgb;
    if (rule == 1) {
        if (s > 1.5) col = uCol3.rgb; else if (s > 0.5) col = mix(uCol1.rgb, uCol2.rgb, t);
    } else if (rule == 2) {
        if (s > 2.5) col = uCol3.rgb; else if (s > 1.5) col = uCol2.rgb; else if (s > 0.5) col = uCol1.rgb;
    } else {
        if (s > 0.5) col = mix(uCol1.rgb, uCol2.rgb, t);
        else col = mix(uCol0.rgb, uCol2.rgb, c.b*uM.w);
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
