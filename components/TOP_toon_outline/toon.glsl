// in0 source, in1 edge mask (rgb = edge strength, blurred glow in in2)
uniform vec4 uA; // x levels  y edge strength mix  z style (0 ink,1 neon) w mix with original
uniform vec4 uB; // edge colour rgb, w glow amount
uniform vec4 uC; // x posterize softness y paper/bg darkening for neon z keep colour
out vec4 fragColor;
vec3 rgb2hsv(vec3 c){ vec4 K=vec4(0.,-1./3.,2./3.,-1.); vec4 p=mix(vec4(c.bg,K.wz),vec4(c.gb,K.xy),step(c.b,c.g)); vec4 q=mix(vec4(p.xyw,c.r),vec4(c.r,p.yzx),step(p.x,c.r)); float d=q.x-min(q.w,q.y); float e=1e-10; return vec3(abs(q.z+(q.w-q.y)/(6.*d+e)),d/(q.x+e),q.x); }
vec3 hsv2rgb(vec3 c){ vec3 k=clamp(abs(fract(c.x+vec3(0.,2./3.,1./3.))*6.-3.)-1.,0.,1.); return c.z*mix(vec3(1.),k,c.y); }
void main(){
  vec2 uv=vUV.st;
  vec3 s=texture(sTD2DInputs[0],uv).rgb;
  float e=texture(sTD2DInputs[1],uv).r;
  float glow=texture(sTD2DInputs[2],uv).r;
  // toon shading: posterize value (keep hue/sat)
  float L=max(uA.x,2.);
  vec3 hsv=rgb2hsv(clamp(s,0.,1.));
  float v=hsv.z*L; float fl=floor(v); float fr=fract(v);
  float k=max(uC.x,.001);
  hsv.z=(fl+smoothstep(.5-k,.5+k,fr))/L;
  vec3 toon=hsv2rgb(hsv);
  vec3 base=mix(s,toon,step(.5,uA.x));
  if(uA.x<2.5) base=toon;
  vec3 col;
  if(uA.z<.5){            // ink: dark lines over the toon image
    col=mix(toon,uB.rgb,clamp(e,0.,1.));
  } else {                // neon: dim image, additive coloured glow + hot core
    vec3 dim=toon*uC.y;
    col=dim+uB.rgb*(e*1.5+glow*uB.w*2.)+vec3(e*e)*.6;
  }
  fragColor=TDOutputSwizzle(vec4(mix(s,col,uA.w),1.));
}
