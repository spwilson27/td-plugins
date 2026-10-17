// Initial boid positions = the input points' P. in0 = size_ref (side x side), in1 = POP to TOP (square layout) of the input P.
out vec4 fragColor;
uniform float uSide;
uniform float uCount;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    int idx = ip.y * int(uSide) + ip.x;
    ivec2 sz = textureSize(sTD2DInputs[1], 0);
    vec3 p = vec3(0.0);
    if (float(idx) < uCount) p = texelFetch(sTD2DInputs[1], ivec2(idx % sz.x, idx / sz.x), 0).xyz;
    fragColor = TDOutputSwizzle(vec4(p, 1.0));
}
