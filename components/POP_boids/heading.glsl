// Unit heading (rgb) from velocity. in0 = velocity.
out vec4 fragColor;
void main(){
    vec3 v = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0).xyz;
    fragColor = TDOutputSwizzle(vec4(normalize(v + vec3(1e-5, 0.0, 0.0)), 1.0));
}
