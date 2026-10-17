// Animated default source: moving textured discs + rotating bar with HDR cores
uniform float uTime;
uniform float uBg;
uniform vec4 uM; // x unused, y mono, z accent, w unused
out vec4 fragColor;
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }
vec3 hsv(float h,float s,float v){
  if(uM.y > .5){ float g = v*(0.35 + 0.65*fract(h*3.0)); return vec3(g)*vec3(.96,.94,.89)*0.9; }   // mono: bone-white greys
  vec3 k=clamp(abs(fract(h+vec3(0.,2./3.,1./3.))*6.-3.)-1.,0.,1.); return v*mix(vec3(1.),k,s); }
void main(){
  vec2 uv=vUV.st;
  float asp=uTDOutputInfo.res.z/uTDOutputInfo.res.w;
  vec2 p=(uv-.5)*vec2(asp,1.);
  float t=uTime;
  float td_ = t;   // slow hue drift
  vec3 bgc = uM.y > .5 ? vec3(0.) : vec3(1.);
  vec3 col=uBg*bgc*(0.10+0.10*hsv(uv.x*.5+td_*.02,.6,1.)+0.10*vn(p*7.));
  if(uM.y > .5) col = vec3(0.012)*step(.5,fract(p.y*14.))*step(.5,fract(p.x*14.)) + vec3(0.02)*vn(p*7.)*uBg;
  col+=uBg*bgc*0.06*step(.5,fract(p.y*14.))*step(.5,fract(p.x*14.));
  float cov=0.;
  // rotating bar
  {
    float a=t*.7; vec2 q=p-vec2(0.,-.18); q=mat2(cos(a),-sin(a),sin(a),cos(a))*q;
    float m=step(abs(q.x),.42)*step(abs(q.y),.03);
    vec3 c=hsv(.55+.1*sin(t),.7,1.0)*(1.+2.*step(.3,abs(q.x))*1.0)*(0.7+0.3*step(.5,fract(q.x*12.)));
    if(uM.y > .5) c = mix(c, vec3(1.0,0.04,0.04)*(1.+2.*step(.3,abs(q.x))), uM.z);
    col=mix(col,c,m); cov=max(cov,m);
  }
  for(int i=0;i<5;i++){
    float fi=float(i);
    vec2 c=vec2(sin(t*(.35+.11*fi)+fi*1.7)*.55*asp*.8, cos(t*(.27+.09*fi)+fi*2.3)*.33);
    float r=.11+.025*fi;
    vec2 q=p-c; float d=length(q);
    float m=smoothstep(r,r-.006,d);
    float tex=vn(q*22.+fi*7.)*.6+.4*step(.5,fract((q.x+q.y)*18.));
    vec3 cc=hsv(.12*fi+td_*.03,.85,.35+.65*tex);
    cc+=vec3(1.,.9,.7)*3.*smoothstep(r*.45,0.,d);
    if(uM.y > .5 && i==2) cc = mix(cc, vec3(1.0,0.04,0.04)*(0.6+3.*smoothstep(r*.45,0.,d)), uM.z);
    col=mix(col,cc,m); cov=max(cov,m);
  }
  fragColor=TDOutputSwizzle(vec4(col,max(cov,0.)));
}
