// External force field (cells/step before dt). in0 = image (edges push flow along them), in1 = optional force/velocity TOP (rg).
out vec4 fragColor;
uniform float uEdge, uForceIn, uHas2, uResScale;
float lum(vec3 c){ return dot(c, vec3(0.299,0.587,0.114)); }
void main(){
    vec2 px = 1.0/vec2(textureSize(sTD2DInputs[0],0)); vec2 uv = vUV.st;
    float l  = lum(texture(sTD2DInputs[0], uv-vec2(px.x,0)).rgb), r = lum(texture(sTD2DInputs[0], uv+vec2(px.x,0)).rgb);
    float b  = lum(texture(sTD2DInputs[0], uv-vec2(0,px.y)).rgb), t = lum(texture(sTD2DInputs[0], uv+vec2(0,px.y)).rgb);
    vec2 g = vec2(r-l, t-b);
    vec2 f = uEdge * uResScale * vec2(-g.y, g.x) * 4.0;          // flow runs along image edges
    f += uHas2 * uForceIn * uResScale * texture(sTD2DInputs[1], uv).xy;
    fragColor = TDOutputSwizzle(vec4(f, 0.0, 1.0));
}
