// jelly_material: gummy translucent look - wrap lighting, fake SSS (thickness approx), rim glow, Beer-Lambert absorption
uniform vec4 uJelly;  // wrap, translucency, rimglow, absorption
uniform vec4 uCol;    // tint rgb, thickness scale
uniform vec4 uCol2;   // absorb colour rgb (deep colour), spec power
uniform vec4 uEnv;    // env intensity, inner noise amount, phase, noise scale
in vec3 vWPos;
in vec3 vWNrm;
in vec3 vObj;
in vec3 vCam;
layout(location = 0) out vec4 fragColor;
#define TAU 6.28318530718
float h31(vec3 p){ p=fract(p*vec3(.1031,.1030,.0973)); p+=dot(p,p.yxz+33.33); return fract((p.x+p.y)*p.z); }
float vn3(vec3 p){ vec3 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(mix(h31(i),h31(i+vec3(1,0,0)),f.x),mix(h31(i+vec3(0,1,0)),h31(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(h31(i+vec3(0,0,1)),h31(i+vec3(1,0,1)),f.x),mix(h31(i+vec3(0,1,1)),h31(i+vec3(1,1,1)),f.x),f.y),f.z); }
float box(vec2 q, vec2 c, vec2 h, float s){ vec2 d=abs(q-c)-h; return 1.-smoothstep(-s,s,max(d.x,d.y)); }
vec3 envP(vec3 d){
  float az=atan(d.x,-d.z)/TAU; float el=asin(clamp(d.y,-1.,1.))/3.14159265;
  float s=.03;
  vec3 c=mix(vec3(.02),vec3(.25,.27,.3),smoothstep(-.3,.5,el));
  c+=vec3(1.)*box(vec2(az,el),vec2(0.,.3),vec2(.3,.04),s)*1.5;
  c+=vec3(1.,.95,.9)*box(vec2(az,el),vec2(.25,0.),vec2(.03,.3),s)*1.6;
  return c;
}
void main(){
  vec3 N=normalize(vWNrm);
  vec3 V=normalize(vCam-vWPos);
  if(dot(N,V)<0.) N=-N;
  float NV=clamp(dot(N,V),0.,1.);
  vec3 L1=normalize(vec3(-.5,.8,.7)), L2=normalize(vec3(.8,.1,-.5));
  // wrap diffuse
  float w=uJelly.x;
  float d1=clamp((dot(N,L1)+w)/(1.+w),0.,1.), d2=clamp((dot(N,L2)+w)/(1.+w),0.,1.);
  // thickness approximation: centre of the shape (facing the viewer) is "thick", silhouettes thin; modulated by noise
  float th=uEnv.z*TAU;
  float nz=vn3(vObj*uEnv.w+vec3(cos(th),sin(th),cos(th+2.))*.8);
  float thick=uCol.w*(.25+.75*pow(NV,.8))*(1.+uEnv.y*(nz-.5)*1.4);
  vec3 absorb=exp(-thick*uJelly.w*(vec3(1.)-uCol2.rgb)*1.6);   // Beer-Lambert towards the deep colour
  vec3 body=uCol.rgb*(d1*vec3(1.,.97,.93)+d2*.5*vec3(.7,.85,1.))*.8;
  // back-light translucency (Barre-Jones): light bleeding through from behind
  vec3 hb=normalize(L1+N*.5); float back=pow(clamp(dot(V,-hb),0.,1.),3.)*uJelly.y;
  vec3 hb2=normalize(L2+N*.5); back+=pow(clamp(dot(V,-hb2),0.,1.),3.)*uJelly.y*.6;
  vec3 sss=uCol.rgb*back*1.6*mix(vec3(1.),uCol2.rgb*1.6,.4);
  vec3 col=body*absorb*1.1+sss;
  col+=mix(uCol.rgb,uCol2.rgb,.5)*(.10+.12*nz*uEnv.y)*(1.-absorb)*2.;                     // inner scattered glow where it is thickest
  // rim glow
  float rim=pow(1.-NV,3.);
  col+=mix(uCol.rgb,vec3(1.),.4)*rim*uJelly.z;
  // specular + reflection
  vec3 R=reflect(-V,N);
  vec3 H1=normalize(L1+V),H2=normalize(L2+V);
  float sp=pow(max(dot(N,H1),0.),uCol2.w)*1.6+pow(max(dot(N,H2),0.),uCol2.w*.5)*.6;
  col+=vec3(1.)*sp;
  float fr=.04+.96*pow(1.-NV,5.);
  col+=envP(R)*fr*uEnv.x;
  col=col/(1.+col*.15);
  vec4 oc=TDDither(vec4(col,1.));
  TDAlphaTest(oc.a);
  fragColor=TDOutputSwizzle(oc);
}
