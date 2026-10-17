// in0 src, in1..5 bloom blurs (small..large), in6 glare
uniform vec4 uA; // x exposure(stops) y tonemap idx z bloom amount w glare amount
uniform vec4 uB; // x chromatic y vignette z vignette softness w grain
uniform vec4 uC; // x grain size(px) y time z gamma w bloom tilt
out vec4 fragColor;
vec3 aces(vec3 x){ return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.); }
vec3 hable(vec3 x){ const float A=.15,B=.5,C=.1,D=.2,E=.02,F=.3; return ((x*(A*x+C*B)+D*E)/(x*(A*x+B)+D*F))-E/F; }
float hash(vec3 p){ p=fract(p*.1031); p+=dot(p,p.zyx+31.32); return fract((p.x+p.y)*p.z); }
void main(){
  vec2 uv=vUV.st; vec2 d=uv-.5;
  float ca=uB.x*.012;
  vec2 o=d*ca*length(d)*4.;
  vec3 c=vec3(texture(sTD2DInputs[0],uv+o).r,texture(sTD2DInputs[0],uv).g,texture(sTD2DInputs[0],uv-o).b);
  vec3 bl=vec3(0.);
  float w[5]=float[5](1.,1.,1.,1.,1.);
  for(int i=0;i<5;i++) bl+=texture(sTD2DInputs[1+i],uv).rgb*(1.+uC.w*float(i));
  bl/=5.;
  vec3 gl=texture(sTD2DInputs[6],uv).rgb;
  c=(c+bl*uA.z*2.+gl*uA.w)*exp2(uA.x);
  int tm=int(uA.y+.5);
  if(tm==1) c=aces(c);
  else if(tm==2){ c=hable(c*2.)/hable(vec3(11.2)); }
  else if(tm==3) c=c/(1.+c);
  c=pow(max(c,0.),vec3(1./max(uC.z,.01)));
  // vignette
  float v=smoothstep(.75,.75-uB.z*.6-.05,length(d*vec2(1.,1.)*1.2));
  c*=mix(1.,v,uB.y);
  // grain
  vec2 gp=floor(uv*uTDOutputInfo.res.zw/max(uC.x,1.));
  float n=hash(vec3(gp,floor(uC.y*24.)))-.5;
  float lum=dot(c,vec3(.3,.59,.11));
  c+=n*uB.w*(1.-.5*lum);
  fragColor=TDOutputSwizzle(vec4(c,1.));
}
