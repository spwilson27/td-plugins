// neon style compositing: in0 source, in1 edge mask, in2 blurred edge mask (glow), in3 posterize ratio (Lookup TOP, toon = source * ratio)
uniform vec4 uA; // rgb edge colour, w glow gain (Glowamount * 2 * (1 + 2*beat))
uniform vec4 uC; // x dim (brightness of the toon image)
out vec4 fragColor;
void main(){
  vec2 uv=vUV.st;
  vec3 s=texture(sTD2DInputs[0],uv).rgb*texture(sTD2DInputs[3],uv).rgb;   // toon image
  float e=texture(sTD2DInputs[1],uv).r;
  float glow=texture(sTD2DInputs[2],uv).r;
  vec3 col=s*uC.x+uA.rgb*(e*1.5+glow*uA.w)+vec3(e*e)*.6;   // dim image + coloured edge and glow + hot white core
  fragColor=TDOutputSwizzle(vec4(col,1.));
}
