// liquid chrome: raymarched metaball SDF, procedural studio env or equirect in1 env
uniform vec4 uA; // ph, blobs, morphcycles, disp
uniform vec4 uB; // rough, irid, envrot(turns), hasEnv
uniform vec4 uC; // camdist, camrot(turns), camheight, tint
out vec4 fragColor;
#define TAU 6.28318530718
float TH;
float smin(float a,float b,float k){ float h=max(k-abs(a-b),0.)/k; return min(a,b)-h*h*k*.25; }
float sdf(vec3 p){
  float th=TH*max(floor(uA.z+.5),0.);
  int nb=int(uA.y+.5);
  float d=1e3;
  for(int i=0;i<8;i++){
    if(i>=nb) break;
    float fi=float(i);
    float k1=1.+mod(fi,2.), k2=1.+mod(fi+1.,3.), k3=1.+mod(fi*2.,2.);
    vec3 c=vec3(sin(th*k1+fi*1.7), cos(th*k2+fi*2.3), sin(th*k3+fi*0.9+1.))*vec3(0.75,0.55,0.7)*(nb==1?0.:1.);
    float r=0.62+0.1*sin(fi*3.1);
    d=smin(d,length(p-c)-r,1.1);
  }
  // periodic displacement (all temporal terms are integer multiples of th)
  float dd=uA.w;
  float n=sin(p.x*3.1+th*2.)*sin(p.y*2.7-th)*sin(p.z*3.3+th*3.)
         +0.5*sin(p.x*6.3-p.z*5.1+th*4.)*sin(p.y*6.7+p.x*2.+th*2.);
  return d+dd*0.25*n;
}
vec3 nrm(vec3 p){ vec2 e=vec2(1,-1)*.0015;
  return normalize(e.xyy*sdf(p+e.xyy)+e.yyx*sdf(p+e.yyx)+e.yxy*sdf(p+e.yxy)+e.xxx*sdf(p+e.xxx)); }
float box(vec2 q, vec2 c, vec2 h, float s){ vec2 d=abs(q-c)-h; return 1.-smoothstep(-s,s,max(d.x,d.y)); }
vec3 envProc(vec3 d,float rough){
  float az=atan(d.x,-d.z)/TAU+uB.z; az=fract(az+.5)-.5;       // -.5..0.5 turns
  float el=asin(clamp(d.y,-1.,1.))/3.14159265;                // -.5..0.5
  float s=.004+rough*.18;
  vec3 c=mix(vec3(.015,.016,.02),vec3(.22,.24,.28),smoothstep(-.3,.5,el));       // gradient sky
  c+=vec3(.20,.2,.22)*smoothstep(.0,-.5,el)*.35;                                    // floor bounce
  c+=vec3(.9)*box(vec2(az,el),vec2(0.,.30),vec2(.32,.035),s)*1.6;                   // top strip
  c+=vec3(1.0,.96,.9)*box(vec2(az,el),vec2(.25,.0),vec2(.025,.30),s)*1.8;           // tall softbox right
  c+=vec3(.85,.92,1.)*box(vec2(az,el),vec2(-.27,.05),vec2(.04,.22),s)*1.5;          // cool box left
  c+=vec3(1.,.15,.1)*box(vec2(az,el),vec2(.5,.1),vec2(.02,.16),s)*1.5;               // red accent rear
  c+=vec3(.8)*box(vec2(az,el),vec2(0.,-.32),vec2(.4,.012),s)*1.2;                    // floor strip
  return c;
}
vec3 envTex(vec3 d,float rough){
  float az=atan(d.x,-d.z)/TAU+uB.z; float el=asin(clamp(d.y,-1.,1.))/3.14159265;
  vec2 uv=vec2(az+.5,el+.5); vec3 c=vec3(0.); float w=rough*.04;
  c+=texture(sTD2DInputs[0],uv).rgb*2.;
  c+=texture(sTD2DInputs[0],uv+vec2(w,0.)).rgb; c+=texture(sTD2DInputs[0],uv-vec2(w,0.)).rgb;
  c+=texture(sTD2DInputs[0],uv+vec2(0.,w)).rgb; c+=texture(sTD2DInputs[0],uv-vec2(0.,w)).rgb;
  return c/6.;
}
vec3 env(vec3 d,float rough){ return uB.w>.5 ? envTex(d,rough) : envProc(d,rough); }
vec3 film(float cosT,float t){ // thin-film rainbow
  vec3 ph=vec3(0.,.33,.67);
  return .5+.5*cos(TAU*(t*vec3(1.,1.1,1.25)*(1.5/ max(cosT,.15))*.5+ph+ (1.-cosT)));
}
void main(){
  TH=uA.x*TAU;
  vec2 uv=vUV.st*2.-1; uv.x*=uTDOutputInfo.res.z/uTDOutputInfo.res.w;
  float ca=uC.y*TAU;
  vec3 ro=vec3(sin(ca),uC.z,cos(ca)); ro=normalize(ro)*uC.x;
  vec3 fw=normalize(-ro), rt=normalize(cross(fw,vec3(0,1,0))), up=cross(rt,fw);
  vec3 rd=normalize(fw*1.8+rt*uv.x+up*uv.y);
  float t=0.; bool hit=false;
  for(int i=0;i<90;i++){ float h=sdf(ro+rd*t); if(h<.0008){hit=true;break;} t+=h*.9; if(t>12.) break; }
  vec3 col=env(rd,0.5)*0.0;
  vec3 bg=vec3(.012)+vec3(.02)*(1.-length(uv)*.5);
  col=bg;
  if(hit){
    vec3 p=ro+rd*t, n=nrm(p);
    float cosT=clamp(dot(-rd,n),0.,1.);
    float fr=pow(1.-cosT,5.);
    vec3 r=reflect(rd,n);
    vec3 e=env(r,uB.x);
    vec3 base=mix(vec3(.88,.9,.95),vec3(.95),0.);
    vec3 F=mix(base,vec3(1.),fr);
    vec3 refl=e*F;
    if(uB.y>0.){
      vec3 f=film(cosT, 1.0+0.5*dot(n,vec3(.3,.7,.2))+0.15*sin(p.y*4.+TH));
      refl*=mix(vec3(1.),f*1.6,uB.y);
      refl+=e*f*fr*uB.y*.6;
    }
    // soft internal darkening in concavities (ao-ish)
    float ao=clamp(.5+.5*(sdf(p+n*.2)/.2),0.,1.);
    refl*=mix(.55,1.,ao);
    col=refl*(1.-uB.x*.25);
    col=mix(col,col*vec3(1.,.9,.85)*1.,uC.w*0.);
  }
  col=col/(1.+col*.25);              // soft shoulder
  col=pow(col,vec3(.95));
  fragColor=TDOutputSwizzle(vec4(col,1.));
}
