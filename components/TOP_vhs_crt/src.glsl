// Animated default source (repeats every 8 s). Dark, bone-white, red accent. HDR-ish cores.
uniform vec4 uP;   // x time in 8 s units, y 8, z 240
out vec4 fragColor;
const float TAU=6.2831853;
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }
void main(){
  vec2 uv=vUV.st;
  float asp=uTDOutputInfo.res.z/uTDOutputInfo.res.w;
  vec2 p=(uv-.5)*vec2(asp,1.);
  float a=TAU*uP.x;
  float n=vn(p*5.+1.5*vec2(cos(a),sin(a)))*.6+vn(p*13.-2.*vec2(sin(a),cos(a))+7.)*.4;
  vec3 col=vec3(.025)+.10*n*vec3(.9,.92,1.);
  col+=.05*step(.5,fract(p.y*12.))*step(.5,fract(p.x*12.));
  col+=.03*smoothstep(.02,.0,abs(fract(p.x*6.)-.5)-.48);
  // discs with radial gradients
  for(int i=0;i<6;i++){
    float fi=float(i);
    float k1=1.+mod(fi,2.), k2=1.+mod(fi+1.,3.)*.0+floor(fi/3.);
    vec2 c=vec2(sin(a*k1+fi*1.7)*.5*asp*.8, cos(a*k2+fi*2.3)*.30);
    float r=.10+.025*fi;
    float d=length(p-c);
    float body=smoothstep(r,r-.004,d);
    float g=1.-d/r;
    vec3 tone=(i==2)?vec3(1.,.08,.05):vec3(.92,.9,.84);
    col=mix(col,tone*(.15+1.1*g*g),body);
    col+=tone*.7*smoothstep(.006,.0,abs(d-r*1.35))*(.5+.5*sin(a*3.+fi));
  }
  // rotating bar
  {
    vec2 q=p-vec2(0.,-.2); float b=a; q=mat2(cos(b),-sin(b),sin(b),cos(b))*q;
    float m=step(abs(q.x),.4)*step(abs(q.y),.025);
    col=mix(col,vec3(.9,.9,.85)*(.5+.9*step(.5,fract(q.x*10.))),m);
  }
  // sweeping scan line
  float sy=fract(uP.x);
  col+=vec3(.4)*smoothstep(.01,.0,abs(uv.y-sy));
  // ramp strip at the top for range
  if(uv.y>.93) col=vec3(uv.x)*vec3(1.,.98,.95);
  fragColor=TDOutputSwizzle(vec4(col,1.));
}
