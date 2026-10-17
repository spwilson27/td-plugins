// tracker_hud pass A: pick N stable feature points (bright local maxima) -> 64x1 float texture (x,y,id,valid)
uniform vec4 uA; // ph, points, threshold, refresh(per loop)
uniform vec4 uB; // jitter(0..1), unused
out vec4 fragColor;
#define TAU 6.28318530718
float h(float n){ return fract(sin(n*12.9898+4.1414)*43758.5453); }
float lum(vec2 uv){ return dot(texture(sTD2DInputs[0],uv).rgb,vec3(.299,.587,.114)); }
float lumb(vec2 uv){ vec2 e=vec2(.002,.003);
  return (lum(uv)*2.+lum(uv+vec2(e.x,0))+lum(uv-vec2(e.x,0))+lum(uv+vec2(0,e.y))+lum(uv-vec2(0,e.y)))/6.; }
void main(){
  float i=floor(gl_FragCoord.x);
  if(i>=uA.y){ fragColor=vec4(0.); return; }
  float ep=uA.w>0.5? mod(floor(uA.x*uA.w+1e-4),uA.w): 0.;
  vec2 best=vec2(.5); float bl=-1.; bool ok=false;
  for(int t=0;t<10;t++){
    float ft=float(t);
    vec2 c=vec2(h(i*7.13+ft*3.37+ep*13.7+1.3),h(i*5.71+ft*2.91+ep*11.1+7.7));
    c=mix(vec2(.05,.07),vec2(.95,.93),c);
    float l=lumb(c);
    if(l>bl){ bl=l; best=c; }
    if(l>uA.z){ best=c; ok=true; break; }
  }
  // hill-climb to the local brightness maximum (feature point)
  vec2 p=best;
  for(int s=0;s<2;s++){
    float r=.012/float(s+1);
    vec2 bp=p; float bv=lumb(p);
    for(int k=0;k<8;k++){ float a=float(k)*TAU/8.; vec2 q=p+vec2(cos(a),sin(a)*1.6)*r*vec2(.5625*1.0+.4375,1.);
      float v=lumb(q); if(v>bv){ bv=v; bp=q; } }
    p=bp;
  }
  float th=uA.x*TAU;
  p+=uB.x*.006*vec2(sin(th*2.+i*1.7),cos(th*3.+i*2.3));
  float id=floor(h(i*3.7+ep*9.1+42.)*90000.)+10000.;
  fragColor=vec4(p,id,(ok||bl>uA.z*.6)?1.:0.);
}
