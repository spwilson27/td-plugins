// Gray-Scott. Input0 = previous state (A,B). Run Steps times per frame via the TOP's Num Passes.
out vec4 fragColor;
uniform float uFeed;
uniform float uKill;
uniform float uDa;
uniform float uDb;
uniform float uDt;
uniform float uPlay;
void main(){
    vec2 px = 1.0 / vec2(textureSize(sTD2DInputs[0], 0));
    vec2 uv = vUV.st;
    vec4 c = texture(sTD2DInputs[0], uv);
    if (uPlay < 0.5) { fragColor = TDOutputSwizzle(c); return; }
    vec2 lap = -c.rg;
    lap += 0.2  * (texture(sTD2DInputs[0], uv+vec2( px.x,0)).rg + texture(sTD2DInputs[0], uv+vec2(-px.x,0)).rg
                 + texture(sTD2DInputs[0], uv+vec2(0, px.y)).rg + texture(sTD2DInputs[0], uv+vec2(0,-px.y)).rg);
    lap += 0.05 * (texture(sTD2DInputs[0], uv+px).rg + texture(sTD2DInputs[0], uv-px).rg
                 + texture(sTD2DInputs[0], uv+vec2(px.x,-px.y)).rg + texture(sTD2DInputs[0], uv+vec2(-px.x,px.y)).rg);
    float a = c.r, b = c.g;
    float abb = a*b*b;
    float na = a + (uDa*lap.x - abb + uFeed*(1.0-a)) * uDt;
    float nb = b + (uDb*lap.y + abb - (uKill+uFeed)*b) * uDt;
    fragColor = TDOutputSwizzle(vec4(clamp(na,0.0,1.0), clamp(nb,0.0,1.0), 0.0, 1.0));
}
