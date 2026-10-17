// Input image -> attractor field (0..1). in0 = image.
uniform vec4 uF;   // x=invert y=power
out vec4 fragColor;
void main(){
    vec4 c = texture(sTD2DInputs[0], vUV.st);
    float l = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722));
    l = clamp(l, 0.0, 1.0);
    if (uF.x > 0.5) l = 1.0 - l;
    l = pow(l, uF.y);
    fragColor = TDOutputSwizzle(vec4(l, l, l, 1.0));
}
