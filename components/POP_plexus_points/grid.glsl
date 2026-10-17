out vec4 fragColor;
uniform vec4 uA;   // opacity, cell size (in height units)
void main(){
  vec2 res = uTDOutputInfo.res.zw;
  vec2 g = (vUV.st*res)/(uA.y*res.y);
  vec2 p = fract(g+0.5)-0.5;                  // 0 at lattice points
  float px = 0.7/(uA.y*res.y);
  float cr = max(step(abs(p.x), px)*step(abs(p.y), 0.09), step(abs(p.y), px)*step(abs(p.x), 0.09));
  float ln = max(step(abs(p.x), px*0.5), step(abs(p.y), px*0.5))*0.12;
  vec3 col = vec3(0.6)*(cr + ln)*uA.x;
  fragColor = TDOutputSwizzle(vec4(col,1.0));
}
