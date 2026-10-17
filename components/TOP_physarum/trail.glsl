// Trail map: diffuse + decay + deposit. in0 = previous trail, in1 = deposit render.
uniform vec4 uT;   // x=diffuse y=decay z=play
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec2 px = uTDOutputInfo.res.xy;
    vec4 c = texture(sTD2DInputs[0], uv);
    if (uT.z < 0.5) { fragColor = c; return; }
    vec4 b = c*4.0;
    b += texture(sTD2DInputs[0], uv+vec2(px.x,0.0))*2.0;
    b += texture(sTD2DInputs[0], uv-vec2(px.x,0.0))*2.0;
    b += texture(sTD2DInputs[0], uv+vec2(0.0,px.y))*2.0;
    b += texture(sTD2DInputs[0], uv-vec2(0.0,px.y))*2.0;
    b += texture(sTD2DInputs[0], uv+px);
    b += texture(sTD2DInputs[0], uv-px);
    b += texture(sTD2DInputs[0], uv+vec2(px.x,-px.y));
    b += texture(sTD2DInputs[0], uv+vec2(-px.x,px.y));
    b /= 16.0;
    float v = mix(c.r, b.r, uT.x)*uT.y + texture(sTD2DInputs[1], uv).r;
    fragColor = TDOutputSwizzle(vec4(v, 0.0, 0.0, 1.0));
}
