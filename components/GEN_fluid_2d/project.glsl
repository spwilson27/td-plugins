// in0 = advected velocity, in1 = pressure. Subtract pressure gradient; walls at border.
out vec4 fragColor;
void main(){
    vec2 px = 1.0/vec2(textureSize(sTD2DInputs[0],0)); vec2 uv = vUV.st;
    float L = texture(sTD2DInputs[1], uv-vec2(px.x,0)).x, R = texture(sTD2DInputs[1], uv+vec2(px.x,0)).x;
    float B = texture(sTD2DInputs[1], uv-vec2(0,px.y)).x, T = texture(sTD2DInputs[1], uv+vec2(0,px.y)).x;
    vec2 v = texture(sTD2DInputs[0], uv).xy - 0.5*vec2(R-L, T-B);
    if (uv.x < px.x || uv.x > 1.0-px.x) v.x = 0.0;
    if (uv.y < px.y || uv.y > 1.0-px.y) v.y = 0.0;
    fragColor = TDOutputSwizzle(vec4(v,0,1));
}
