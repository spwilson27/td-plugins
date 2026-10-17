// glass_refraction: raymarched glass shape refracting in1 with per-channel IOR, frost, highlights
uniform vec4 uA; // ph, ior, dispersion, frost
uniform vec4 uB; // size, shape(0 morph,1 torus,2 cube), morphcycles, spin
uniform vec4 uC; // highlights, camdist, bgscale, thicknessAbsorb
out vec4 fragColor;
#define TAU 6.28318530718
float TH;
mat3 rotY(float a){ float c=cos(a),s=sin(a); return mat3(c,0,-s,0,1,0,s,0,c); }
mat3 rotX(float a){ float c=cos(a),s=sin(a); return mat3(1,0,0,0,c,s,0,-s,c); }
float sdRB(vec3 p,vec3 b,float r){ vec3 q=abs(p)-b; return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.)-r; }
float sdTor(vec3 p,vec2 t){ vec2 q=vec2(length(p.xz)-t.x,p.y); return length(q)-t.y; }
float sdf(vec3 p){
  float k=max(floor(uB.z+.5),0.);
  p=rotY(TH*floor(uB.w+.5))*rotX(TH*floor(uB.w+.5)*0.+.5+.3*sin(TH))*p;
  float s=uB.x;
  p/=s;
  float m=.5+.5*sin(TH*k);
  p.x+=.08*sin(p.y*3.+TH*k*2.); p.y+=.08*sin(p.z*3.-TH*k);   // soft wobble
  float d;
  if(uB.y<.5)      d=mix(length(p)-.85, sdRB(p,vec3(.55),.3), m);
  else if(uB.y<1.5)d=sdTor(p,vec2(.7,.3+.12*m));
  else             d=sdRB(p,vec3(.55),.12+.25*m);
  return d*s;
}
vec3 nrm(vec3 p){ vec2 e=vec2(1,-1)*.002;
  return normalize(e.xyy*sdf(p+e.xyy)+e.yyx*sdf(p+e.yyx)+e.yxy*sdf(p+e.yxy)+e.xxx*sdf(p+e.xxx)); }
vec3 bgTap(vec2 uv){ return texture(sTD2DInputs[0],uv).rgb; }
float bgChan(vec2 uv,int ch,float fr){
  float a=0.;
  if(fr<.003) return bgTap(uv)[ch];
  for(int i=0;i<8;i++){
    float fi=float(i)+.5; float r=sqrt(fi/8.)*fr, ang=fi*2.39996;
    a+=bgTap(uv+vec2(cos(ang),sin(ang))*r*vec2(uTDOutputInfo.res.w/uTDOutputInfo.res.z,1.))[ch];
  }
  return a/8.;
}
void main(){
  TH=uA.x*TAU;
  vec2 uv=vUV.st; vec2 q=uv*2.-1; float asp=uTDOutputInfo.res.z/uTDOutputInfo.res.w; q.x*=asp;
  vec3 ro=vec3(0,0,uC.y), rd=normalize(vec3(q*0.5,-1.));   // fov ~ 53 deg
  float t=0.; bool hit=false;
  for(int i=0;i<80;i++){ float h=sdf(ro+rd*t); if(h<.001){hit=true;break;} t+=h; if(t>12.) break; }
  vec2 base=uv; vec3 col;
  float frost=uA.w*.05;
  if(!hit){
    col=vec3(bgChan(base,0,0.),bgChan(base,1,0.),bgChan(base,2,0.));
  } else {
    vec3 p=ro+rd*t; vec3 n=nrm(p);
    float cosT=clamp(dot(-rd,n),0.,1.); float fr=pow(1.-cosT,4.);
    col=vec3(0.);
    float ior0=uA.y;
    // thickness: march inside along the refracted ray
    vec3 rr=refract(rd,n,1./ior0);
    vec3 pi=p-n*.01; float ti=0.;
    for(int i=0;i<40;i++){ float h=-sdf(pi+rr*ti); if(h<.002) break; ti+=max(h,.02); if(ti>5.) break; }
    float thick=ti;
    float strength=(0.05+0.07*clamp(thick,0.,2.5))*uB.x;
    for(int ch=0;ch<3;ch++){
      float ior=ior0+uA.z*(float(ch)-1.)*.5;
      vec3 r1=refract(rd,n,1./ior);
      vec2 off=(r1.xy-rd.xy)*strength/uC.z;            // screen-space bend, inverted image feel through thickness
      vec2 buv=uv+off*vec2(1./asp,1.)*(1.+ (ior-1.)*0.);
      col[ch]=bgChan(buv,ch,frost*(1.+thick*.3));
    }
    // absorption tint with thickness
    col*=exp(-thick*uC.w*vec3(.12,.07,.04));
    // highlights: fresnel rim + two key lights + caustic-ish tight curvature glints
    vec3 L1=normalize(vec3(-.5,.8,.6)), L2=normalize(vec3(.7,.3,.5));
    vec3 hv1=normalize(L1-rd), hv2=normalize(L2-rd);
    float sp=pow(max(dot(n,hv1),0.),600.)*5.+pow(max(dot(n,hv2),0.),250.)*1.5;
    vec3 n2=nrm(p+vec3(.012,.0,.0)); float curv=length(n2-n)*60.;
    float glint=pow(clamp(curv*.15,0.,1.),2.)*fr*2.;
    col+=uC.x*(vec3(1.,.97,.92)*(sp+fr*.7)+vec3(1.,.9,.8)*glint);
    col=mix(col,col*.85,0.);
  }
  col=col/(1.+col*.12);
  fragColor=TDOutputSwizzle(vec4(col,1.));
}
