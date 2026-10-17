// default background for glass_refraction: bone-white typographic bars + grid + red dot, loops on phase
uniform vec4 uP; // ph
out vec4 fragColor;
#define TAU 6.28318530718
float h(float n){ return fract(sin(n*91.3)*43758.5453); }
void main(){
  vec2 uv=vUV.st; float asp=uTDOutputInfo.res.z/uTDOutputInfo.res.w;
  vec2 p=(uv-.5)*vec2(asp,1.); float th=uP.x*TAU;
  vec3 col=vec3(.02);
  // horizontal bars scrolling (integer wrap -> loops)
  float rows=14.; float ry=uv.y*rows; float id=floor(ry);
  float dir=mod(id,2.)<1.?1.:-1.;
  float sx=uv.x*8.+dir*uP.x*8.*(1.+mod(id,3.));  // scroll whole 8-cell periods per loop
  float cell=mod(floor(sx),8.); float on=step(.35,h(cell+id*17.));
  float bar=step(.18,fract(ry))*step(fract(ry),.82)*on*step(fract(sx),.8);
  col+=vec3(.92,.9,.85)*bar*(.55+.45*h(cell*3.+id));
  // fine grid
  col+=vec3(.12)*(step(.97,fract(uv.x*40.))+step(.97,fract(uv.y*22.)));
  // red orbiting dot + ring
  vec2 c=vec2(cos(th),sin(th*2.))*vec2(.45*asp*.6,.28);
  float d=length(p-c);
  col=mix(col,vec3(1.,.08,.05)*2.,smoothstep(.07,.065,d));
  col+=vec3(1.,.1,.05)*.8*smoothstep(.004,0.,abs(d-.14));
  fragColor=TDOutputSwizzle(vec4(col,1.));
}
