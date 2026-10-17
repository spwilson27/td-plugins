// One odd-even transposition sort pass. in0 = previous state, in1 = source.
uniform vec4 uP;   // phase, loop sec, frames/loop
uniform vec4 uS;   // x direction (0 right,1 left,2 up,3 down), y lo, z hi, w key (0 luma,1 hue,2 sat,3 red)
uniform vec4 uT;   // x enabled, y pass index, z frame, w refresh (0..1)
uniform vec4 uU;   // x hard refresh flag, y first pass flag
out vec4 fragColor;
float luma(vec3 c){ return dot(c,vec3(.299,.587,.114)); }
float key(vec3 c){
  int k=int(uS.w+.5);
  if(k==0) return luma(c);
  float mx=max(c.r,max(c.g,c.b)), mn=min(c.r,min(c.g,c.b));
  if(k==2) return (mx-mn)/max(mx,1e-4);
  if(k==3) return c.r;
  float d=mx-mn+1e-5, h;
  if(mx==c.r) h=mod((c.g-c.b)/d,6.); else if(mx==c.g) h=(c.b-c.r)/d+2.; else h=(c.r-c.g)/d+4.;
  return h/6.;
}
bool inr(vec3 c){ float l=luma(c); return l>=uS.y && l<=uS.z; }
vec3 F(ivec2 p, ivec2 sz){
  p=clamp(p,ivec2(0),sz-1);
  vec3 s=texelFetch(sTD2DInputs[1],p,0).rgb;
  if(uU.y<.5) return texelFetch(sTD2DInputs[0],p,0).rgb;    // not first pass: just state
  vec3 st=texelFetch(sTD2DInputs[0],p,0).rgb;
  if(uU.x>.5) return s;
  return mix(st,s,uT.w);
}
void main(){
  ivec2 sz=ivec2(uTDOutputInfo.res.zw);
  ivec2 ip=ivec2(gl_FragCoord.xy);
  vec3 cur=F(ip,sz);
  if(uT.x<.5){ fragColor=TDOutputSwizzle(vec4(cur,1.)); return; }
  int d=int(uS.x+.5);
  bool horiz=(d<2);
  int idx=horiz?ip.x:ip.y;
  int N=horiz?sz.x:sz.y;
  int parity=int(mod(uT.z+uT.y,2.));
  bool lower=(((idx+parity)&1)==0);
  int pidx=lower?idx+1:idx-1;
  if(pidx<0||pidx>=N){ fragColor=TDOutputSwizzle(vec4(cur,1.)); return; }
  ivec2 pp=horiz?ivec2(pidx,ip.y):ivec2(ip.x,pidx);
  vec3 oth=F(pp,sz);
  bool ok=inr(cur)&&inr(oth);
  // dir +1: brighter goes toward higher index
  float dirp=(d==0||d==2)?1.:-1.;
  vec3 a=lower?cur:oth, b=lower?oth:cur;   // a=lower index, b=higher
  float ka=key(a), kb=key(b);
  bool swap=(dirp>0.)?(ka>kb):(ka<kb);
  vec3 o=(ok&&swap)?oth:cur;
  fragColor=TDOutputSwizzle(vec4(o,1.));
}
