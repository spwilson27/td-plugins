// out2: rgb = cell id colour (stable per cell), a = edge distance (0 on the border, 1 deep inside a cell)
uniform vec4 uA; // count, 0,0,0
out vec4 fragColor;
float hash11(float n){ return fract(sin(n*127.1+311.7)*43758.5453); }
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    float aspect = res.x/res.y;
    vec4 c = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    int i1 = int(c.x + 0.5);
    float h = texelFetch(sTD2DInputs[1], ivec2(i1,0), 0).z;
    vec3 id = vec3(hash11(h*91.7+1.3), hash11(h*57.3+7.9), hash11(h*13.1+3.7));
    float cs = sqrt(aspect/max(uA.x,1.));
    float e = clamp(c.w/(cs*0.5), 0., 1.);
    fragColor = TDOutputSwizzle(vec4(id, e));
}
