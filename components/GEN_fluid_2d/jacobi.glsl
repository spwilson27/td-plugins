// in0 = pressure (previous pass), in1 = divergence
out vec4 fragColor;
void main(){
    vec2 px = 1.0/vec2(textureSize(sTD2DInputs[0],0)); vec2 uv = vUV.st;
    float L = texture(sTD2DInputs[0], uv-vec2(px.x,0)).x, R = texture(sTD2DInputs[0], uv+vec2(px.x,0)).x;
    float B = texture(sTD2DInputs[0], uv-vec2(0,px.y)).x, T = texture(sTD2DInputs[0], uv+vec2(0,px.y)).x;
    float d = texture(sTD2DInputs[1], uv).x;
    fragColor = TDOutputSwizzle(vec4((L+R+B+T-d)*0.25,0,0,1));
}
