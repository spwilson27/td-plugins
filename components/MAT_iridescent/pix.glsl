// iridescent_material: thin-film interference + fresnel + anisotropic sheen + oil-slick noise
uniform vec4 uFilm;   // base thickness (nm), thickness variation (nm), film IOR, iridescence amount
uniform vec4 uOil;    // noise scale, noise path radius, phase(loop 0..1+), noise octaves-ish contrast
uniform vec4 uSheen;  // sheen amount, anisotropy (0..1), sheen exponent, fresnel power
uniform vec4 uEnv;    // env rotation (turns), hasEnv, env intensity, roughness
uniform vec4 uBase;   // base tint rgb, substrate IOR
uniform vec4 uExtra;  // brush angle (turns), unused...
uniform sampler2D sEnv;
in vec3 vWPos;
in vec3 vWNrm;
in vec2 vTex;
in vec3 vCam;
layout(location = 0) out vec4 fragColor;
#define TAU 6.28318530718
float h31(vec3 p){ p=fract(p*vec3(.1031,.1030,.0973)); p+=dot(p,p.yxz+33.33); return fract((p.x+p.y)*p.z); }
float vn3(vec3 p){ vec3 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(mix(h31(i),h31(i+vec3(1,0,0)),f.x),mix(h31(i+vec3(0,1,0)),h31(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(h31(i+vec3(0,0,1)),h31(i+vec3(1,0,1)),f.x),mix(h31(i+vec3(0,1,1)),h31(i+vec3(1,1,1)),f.x),f.y),f.z); }
float fbm(vec3 p){ float a=.5,s=0.; for(int i=0;i<4;i++){ s+=a*vn3(p); p=p*2.03+7.1; a*=.5;} return s; }
float box(vec2 q, vec2 c, vec2 h, float s){ vec2 d=abs(q-c)-h; return 1.-smoothstep(-s,s,max(d.x,d.y)); }
vec3 envProc(vec3 d,float rough){
  float az=atan(d.x,-d.z)/TAU+uEnv.x; az=fract(az+.5)-.5;
  float el=asin(clamp(d.y,-1.,1.))/3.14159265;
  float s=.004+rough*.18;
  vec3 c=mix(vec3(.012,.013,.016),vec3(.16,.175,.2),smoothstep(-.3,.5,el));
  c+=vec3(.9)*box(vec2(az,el),vec2(0.,.30),vec2(.32,.035),s)*1.6;
  c+=vec3(1.0,.96,.9)*box(vec2(az,el),vec2(.25,.0),vec2(.025,.30),s)*1.8;
  c+=vec3(.85,.92,1.)*box(vec2(az,el),vec2(-.27,.05),vec2(.04,.22),s)*1.5;
  c+=vec3(1.,.15,.1)*box(vec2(az,el),vec2(.5,.1),vec2(.02,.16),s)*1.2;
  return c;
}
vec3 envTex(vec3 d,float rough){
  float az=atan(d.x,-d.z)/TAU+uEnv.x; float el=asin(clamp(d.y,-1.,1.))/3.14159265;
  vec2 uv2=vec2(az+.5,el+.5);
  return textureLod(sEnv,uv2,rough*6.).rgb;
}
vec3 env(vec3 d,float r){ return uEnv.y>.5 ? envTex(d,r) : envProc(d,r); }
// thin film reflectance per wavelength (Airy, two interfaces)
float filmR(float lambda,float d,float n1,float n2,float cosI){
  float sinI2=1.-cosI*cosI;
  float cosT=sqrt(max(1.-sinI2/(n1*n1),0.));
  float r1=(cosI-n1*cosT)/(cosI+n1*cosT);          // air->film (s-pol)
  float cosS=sqrt(max(1.-sinI2/(n2*n2),0.));
  float r2=(n1*cosT-n2*cosS)/(n1*cosT+n2*cosS);    // film->substrate
  float delta=4.*3.14159265*n1*d*cosT/lambda;
  float c=cos(delta);
  return (r1*r1+r2*r2+2.*r1*r2*c)/(1.+r1*r1*r2*r2+2.*r1*r2*c);
}
void main(){
  vec3 N=normalize(vWNrm);
  vec3 cam=vCam;
  vec3 V=normalize(cam-vWPos);
  if(dot(N,V)<0.) N=-N;
  float cosI=clamp(dot(N,V),0.,1.);
  float th=uOil.z*TAU;
  // oil-slick thickness: noise on a circular path in noise space -> seamless loop
  vec3 np=vWPos*uOil.x+vec3(cos(th),sin(th),cos(th+1.7))*uOil.y;
  float nz=fbm(np);
  float thick=uFilm.x+uFilm.y*(nz*2.-1.)+uFilm.y*.35*sin(vWPos.y*3.+th);
  thick=max(thick,10.);
  vec3 R=vec3(filmR(650.,thick,uFilm.z,uBase.w,cosI),filmR(532.,thick,uFilm.z,uBase.w,cosI),filmR(450.,thick,uFilm.z,uBase.w,cosI));
  R=clamp(R*2.2,0.,1.); // film reflectance (boosted so interference bands read clearly)
  // fresnel (dielectric-ish) amplitude for rainbow rim
  float fr=pow(1.-cosI,uSheen.w);
  vec3 Rv=reflect(-V,N);
  vec3 e=env(Rv,uEnv.w);
  vec3 spec=e*mix(vec3(.9),R,uFilm.w)*(.25+.75*mix(1.,fr,.6)+0.0);
  spec*=uEnv.z;
  // fresnel rainbow at grazing angles: add film colour modulated by rim
  vec3 rim=R*fr*1.4*uFilm.w;
  // anisotropic sheen (Kajiya-Kay) along brushed tangent
  float ba=uExtra.x*TAU;
  vec3 up=abs(N.y)<.95?vec3(0,1,0):vec3(1,0,0);
  vec3 T=normalize(cross(N,up)); vec3 B=cross(N,T);
  T=normalize(T*cos(ba)+B*sin(ba));
  vec3 L1=normalize(vec3(-.4,.8,.6)), L2=normalize(vec3(.8,.2,.4));
  float aniso=0.;
  vec3 H1=normalize(L1+V), H2=normalize(L2+V);
  float tH1=dot(T,H1), tH2=dot(T,H2);
  float kk=pow(sqrt(max(1.-tH1*tH1,0.)),uSheen.z)+.6*pow(sqrt(max(1.-tH2*tH2,0.)),uSheen.z);
  float iso=pow(max(dot(N,H1),0.),uSheen.z)+.6*pow(max(dot(N,H2),0.),uSheen.z);
  aniso=mix(iso,kk*max(dot(N,L1),0.),uSheen.y);
  vec3 sheenC=mix(vec3(1.),R*1.5,uFilm.w)*aniso*uSheen.x;
  vec3 col=uBase.rgb*.03+spec+rim+sheenC;
  col=col/(1.+col*.2);
  vec4 outc=TDDither(vec4(col,1.));
  TDAlphaTest(outc.a);
  fragColor=TDOutputSwizzle(outc);
}
