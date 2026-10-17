// TOP_ssao: colour * AO mask. in0 = colour, in1 = AO mask.
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec4 c = texture(sTD2DInputs[0], uv);
    float m = texture(sTD2DInputs[1], uv).r;
    fragColor = TDOutputSwizzle(vec4(c.rgb * m, c.a));
}
