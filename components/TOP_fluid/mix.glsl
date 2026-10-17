// in0 = dye (smeared image), in1 = original image. Dry/wet.
out vec4 fragColor;
uniform float uMix;
void main(){
    vec2 uv = vUV.st;
    vec4 a = texture(sTD2DInputs[1], uv);
    vec3 w = max(texture(sTD2DInputs[0], uv).rgb, 0.0);
    fragColor = TDOutputSwizzle(vec4(mix(a.rgb, w, uMix), 1.0));
}
