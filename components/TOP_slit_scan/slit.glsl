// in0 = Texture 3D TOP ring buffer (rolling cache, newest = last slice), in1 = displacement map (2D, sampled as sTD2DInputs[0] since in0 is 3D)
uniform vec4 uA; // x frames (depth)  y mode  z direction (+1/-1)  w scroll phase (speed*time)
uniform vec4 uC; // x isPhase
uniform vec4 uB; // x ring size N  y current absolute frame  z noise time  w smooth (0/1)
out vec4 fragColor;
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }
vec3 frameAt(vec2 uv,float age){
  float N=uB.x;
  float s=clamp(N-1.-age,0.,N-1.);          // rolling cache: newest cook is the last slice
  return texture(sTD3DInputs[0],vec3(uv,(floor(s+.5)+.5)/N)).rgb;
}
void main(){
  vec2 uv=vUV.st; int mode=int(uA.y+.5);
  float d;
  if(mode==0) d=uv.x;
  else if(mode==1) d=uv.y;
  else if(mode==2) d=clamp(length(uv-.5)*1.4142,0.,1.);
  else if(mode==3){ vec2 p=uv*vec2(uTDOutputInfo.res.z/uTDOutputInfo.res.w,1.)*2.5; float t=uB.z;
    vec2 o1=vec2(t,0.), o2=vec2(0.,-t*1.3), o3=vec2(t*.7);
    if(uC.x>.5){ o1=1.2*vec2(cos(t),sin(t)); o2=1.2*vec2(cos(2.*t),sin(2.*t)); o3=1.2*vec2(cos(t),-sin(t)); }   // circular offsets -> periodic
    d=vn(p+o1)*.55+vn(p*2.+o2+7.)*.3+vn(p*4.+o3+13.)*.15; d=clamp((d-.2)*1.6,0.,1.); }
  else { vec3 m=texture(sTD2DInputs[0],uv).rgb; d=dot(m,vec3(.299,.587,.114)); }
  if(uA.z<0.) d=1.-d;
  d=abs(fract((d+uA.w)*.5)*2.-1.);          // triangle-wave scroll: seamless animation
  float maxAge=min(uA.x,uB.x-2.);
  float age=d*maxAge;
  vec3 c;
  if(uB.w>.5){ float a0=floor(age); c=mix(frameAt(uv,a0),frameAt(uv,a0+1.),age-a0); }
  else c=frameAt(uv,floor(age+.5));
  fragColor=TDOutputSwizzle(vec4(c,1.));
}
