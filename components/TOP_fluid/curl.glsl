// Input0 = velocity (cells/step in rg). Output: curl in r.
out vec4 fragColor;
void main(){
    vec2 px = 1.0/vec2(textureSize(sTD2DInputs[0],0)); vec2 uv = vUV.st;
    float L = texture(sTD2DInputs[0], uv-vec2(px.x,0)).y;
    float R = texture(sTD2DInputs[0], uv+vec2(px.x,0)).y;
    float B = texture(sTD2DInputs[0], uv-vec2(0,px.y)).x;
    float T = texture(sTD2DInputs[0], uv+vec2(0,px.y)).x;
    fragColor = TDOutputSwizzle(vec4(0.5*((R-L)-(T-B)),0,0,1));
}
