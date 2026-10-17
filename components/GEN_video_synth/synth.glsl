// LZX/Hydra-style oscillator patch. in0 = optional video input (black when unconnected).
// Fully periodic in phase P: oscillator sync/rotation are integer cycles per loop; "feedback" is an
// analytic unrolled echo (taps at earlier phases), so it loops exactly.
uniform vec4 uP;                    // phase, loop sec, frames/loop
uniform vec4 uO0, uO1, uO2;         // x freq, y sync (cycles/loop), z rotation deg, w shape (0 sine,1 square,2 saw)
uniform vec4 uM;                    // x modulate, y kaleid segs, z feedback, w colorize
uniform vec4 uN;                    // x scale, y hue, z contrast, w palette
uniform vec4 uQ;                    // x rotspeed (cycles/loop), y input mix, z echo zoom, w echo rot (deg/tap)
uniform vec4 uR;                    // x echo spacing (loop frac), y input displace, z has input, w gamma
out vec4 fragColor;
const float TAU=6.2831853;
mat2 rot(float a){ float c=cos(a),s=sin(a); return mat2(c,-s,s,c); }
float osc(vec2 p, vec4 o, float P, float scale){
  vec2 r=rot(radians(o.z))*p;
  float ph=o.x*scale*r.x+o.y*P;
  float s=fract(ph);
  if(o.w<.5) return .5+.5*sin(TAU*ph);
  if(o.w<1.5) return smoothstep(.48,.52,s)*smoothstep(1.,.96,s);   // square, anti-aliased
  return s;                                                       // saw
}
vec3 pal(float t, int id){
  t=clamp(t,0.,1.);
  if(id==0) return vec3(.93,.91,.85)*t;                                              // bone
  if(id==1) return mix(vec3(.02,.025,.04),vec3(.75,.82,.9),t)*(.3+.7*smoothstep(0.,.6,t)); // chrome
  if(id==2) return mix(mix(vec3(0.),vec3(.9,.02,.02),smoothstep(0.,.55,t)),vec3(.95,.92,.86),smoothstep(.5,1.,t)); // red->bone
  if(id==3) return .5+.5*cos(TAU*(vec3(1.)*t+vec3(.0,.33,.67)));                      // rainbow
  return .5+.5*cos(TAU*(vec3(1.,.8,.6)*t+vec3(.55,.2,.0)))*vec3(1.,.5,1.);           // acid
}
vec3 scene(vec2 uv, float P){
  float asp=uTDOutputInfo.res.z/uTDOutputInfo.res.w;
  vec2 p=(uv-.5)*vec2(asp,1.);
  p=rot(TAU*P*uQ.x)*p;
  vec3 inp=vec3(0.);
  if(uR.z>.5){ inp=texture(sTD2DInputs[0],uv).rgb; p+=(inp.rg-.5)*uR.y*.4; }
  float seg=uM.y;
  if(seg>=2.){
    float a=atan(p.y,p.x), r=length(p), w=TAU/seg;
    a=mod(a,w); a=abs(a-w*.5);
    p=r*vec2(cos(a),sin(a));
  }
  float sc=uN.x;
  float A=osc(p,uO0,P,sc);
  vec2 pb=p+(A-.5)*uM.x*vec2(.35,.25);
  float B=osc(pb,uO1,P,sc);
  vec2 pc=p+(B-.5)*uM.x*vec2(-.25,.35)+(A-.5)*uM.x*.15;
  float C=osc(pc,uO2,P,sc);
  float l=mix(abs(A-B),C,.35);
  l=mix(l,A*B,.3);
  l=pow(clamp((l-.5)*uN.z+.5,0.,1.),uR.w);
  vec3 col;
  int id=int(uN.w+.5);
  vec3 mono=pal(l+uN.y*0.,id);
  if(uM.w>.001){
    vec3 lc=pow(vec3(clamp((abs(A-B)-.5)*uN.z+.5,0.,1.),l,clamp((abs(B-C)-.5)*uN.z+.5,0.,1.)),vec3(1.));
    vec3 col2=vec3(pal(fract(lc.x+uN.y),id).r,pal(fract(lc.y+uN.y+.07),id).g,pal(fract(lc.z+uN.y+.14),id).b);
    col=mix(mono,col2,uM.w);
  } else col=mono;
  col=mix(col,col*(.4+inp*1.6),uQ.y*uR.z);
  return col;
}
void main(){
  vec2 uv=vUV.st;
  float P=uP.x;
  vec3 acc=scene(uv,P);
  float fb=clamp(uM.z,0.,.95);
  vec2 q=uv-.5;
  float w=1.;
  for(int j=1;j<=7;j++){
    w*=fb;
    float fj=float(j);
    q=rot(radians(uQ.w))*q/uQ.z;
    vec2 u2=q+.5;
    vec3 t=scene(u2,P-fj*uR.x)*w;
    float inb=step(0.,u2.x)*step(u2.x,1.)*step(0.,u2.y)*step(u2.y,1.);
    acc=1.-(1.-acc)*(1.-t*inb);
  }
  fragColor=TDOutputSwizzle(vec4(acc,1.));
}
