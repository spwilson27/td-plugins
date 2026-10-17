out vec4 fragColor;
void main(){
    vec2 px = 1.0/vec2(textureSize(sTD2DInputs[0],0)); vec2 uv = vUV.st;
    vec2 c = texture(sTD2DInputs[0], uv).xy;
    float L = texture(sTD2DInputs[0], uv-vec2(px.x,0)).x, R = texture(sTD2DInputs[0], uv+vec2(px.x,0)).x;
    float B = texture(sTD2DInputs[0], uv-vec2(0,px.y)).y, T = texture(sTD2DInputs[0], uv+vec2(0,px.y)).y;
    // solid walls: mirror normal velocity at the border
    if (uv.x-px.x < 0.0) L = -c.x; if (uv.x+px.x > 1.0) R = -c.x;
    if (uv.y-px.y < 0.0) B = -c.y; if (uv.y+px.y > 1.0) T = -c.y;
    fragColor = TDOutputSwizzle(vec4(0.5*((R-L)+(T-B)),0,0,1));
}
