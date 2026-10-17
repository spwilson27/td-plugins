// false-color. in0 = image, in1 = driver (luminance source: image itself or in2 depth), in2 = palette strip (native Ramp TOPs)
uniform vec4 uP;   // phase, loop sec, frames/loop
uniform vec4 uA;   // x map(0 thermal,1 xray,2 night,3 custom), y gain, z bias, w invert
uniform vec4 uB;   // x edges, y noise, z isotherms, w mix with original
uniform vec4 uC;   // x crosshair, y legend, z target x, w target y
uniform vec4 uD;   // rgb hud color
uniform vec4 uE;   // rgb edge color
out vec4 fragColor;
const float TAU=6.2831853;
float h21(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
float luma(vec3 c){ return dot(c,vec3(.299,.587,.114)); }
float D(vec2 uv){ return luma(texture(sTD2DInputs[1],uv).rgb); }
// palette = in2: a 1024x1 gradient made by native Ramp TOPs (thermal / x-ray / night / custom), picked by the Map parameter
vec3 mapcol(float l, int m, vec2 uv){
  return texture(sTD2DInputs[2], vec2(.0005+.999*clamp(l,0.,1.),.5)).rgb;
}
// tiny line/segment helper
float seg(vec2 p, vec2 a, vec2 b, float w){ vec2 pa=p-a, ba=b-a; float h=clamp(dot(pa,ba)/dot(ba,ba),0.,1.); return smoothstep(w,w*.4,length(pa-ba*h)); }
void main(){
  vec2 uv=vUV.st;
  vec2 res=uTDOutputInfo.res.zw;
  vec2 px=1./res;
  float asp=res.x/res.y;
  float f=floor(uP.x*uP.z);
  float l=D(uv);
  float noise=uB.y;
  // sensor noise: temporal grain + fixed column pattern
  float g=h21(uv*res+f*7.13)-.5;
  float cp=h21(vec2(floor(uv.x*res.x),3.))-.5;
  l+=g*noise*.35+cp*noise*.06;
  l=(l-.5)*uA.y+.5+uA.z;
  if(uA.w>.5) l=1.-l;
  int m=int(uA.x+.5);
  vec3 col=mapcol(l,m,uv);
  // isotherm contour lines
  if(uB.z>0.){
    float q=fract(l*8.);
    float iso=smoothstep(.04,0.,min(q,1.-q));
    col=mix(col,vec3(1.),iso*uB.z*.6);
  }
  // edge overlay (sobel on driver)
  if(uB.x>0.){
    float tl=D(uv+px*vec2(-1,1)), t=D(uv+px*vec2(0,1)), tr=D(uv+px*vec2(1,1));
    float ml=D(uv+px*vec2(-1,0)), mr=D(uv+px*vec2(1,0));
    float bl=D(uv+px*vec2(-1,-1)), b=D(uv+px*vec2(0,-1)), br=D(uv+px*vec2(1,-1));
    float gx=-tl-2.*ml-bl+tr+2.*mr+br, gy=-tl-2.*t-tr+bl+2.*b+br;
    float e=clamp(length(vec2(gx,gy))*3.,0.,1.);
    col=mix(col,uE.rgb*(m==2?vec3(.3,1.,.4):vec3(1.)),e*uB.x);
  }
  // mode-specific post
  if(m==2){
    col*=.8+.2*sin(uv.y*res.y*3.14159);
    float v=length((uv-.5)*vec2(asp,1.));
    col*=smoothstep(.95,.45,v);
    col+=vec3(.0,.04,.01)*(h21(uv*res+f)-.5);
  }
  col=mix(col,texture(sTD2DInputs[0],uv).rgb,uB.w);
  // HUD
  vec2 hp=(uv-.5)*vec2(asp,1.);
  vec3 hc=uD.rgb;
  float hud=0.;
  vec2 tg=(vec2(uC.z,uC.w)-.5)*vec2(asp,1.);
  float lw=1.2*px.y;
  if(uC.x>.5){
    vec2 q=hp-tg;
    float gap=.03, len=.09;
    hud=max(hud,seg(q,vec2(gap,0),vec2(len,0),lw)); hud=max(hud,seg(q,vec2(-gap,0),vec2(-len,0),lw));
    hud=max(hud,seg(q,vec2(0,gap),vec2(0,len),lw)); hud=max(hud,seg(q,vec2(0,-gap),vec2(0,-len),lw));
    float r=length(q);
    hud=max(hud,smoothstep(lw*1.5,0.,abs(r-.055))*step(.5,fract(atan(q.y,q.x)/TAU*16.)));
    for(int i=0;i<4;i++){ float t=float(i)*.0125+.1; hud=max(hud,seg(q,vec2(t,-.006),vec2(t,.006),lw)); hud=max(hud,seg(q,vec2(-t,-.006),vec2(-t,.006),lw)); }
    // level meter next to crosshair showing value at target
    float lt=clamp((D(vec2(uC.z,uC.w))-.5)*uA.y+.5+uA.z,0.,1.);
    vec2 mq=q-vec2(.13,-.05);
    float inbox=step(0.,mq.x)*step(mq.x,.012)*step(0.,mq.y)*step(mq.y,.10);
    hud=max(hud,inbox*(mq.y<lt*.10?.9:.18));
    // corner brackets
    vec2 a=abs(hp)-vec2(.5*asp-.04,.5-.04);
    float cb=0.;
    vec2 s=sign(hp);
    vec2 c0=vec2(.5*asp-.04,.5-.04)*s;
    cb=max(cb,seg(hp,c0,c0-vec2(s.x*.05,0),lw)); cb=max(cb,seg(hp,c0,c0-vec2(0,s.y*.05),lw));
    hud=max(hud,cb);
  }
  if(uC.y>.5){
    // legend bar (right edge)
    vec2 q=uv-vec2(.955,.25);
    if(q.x>0.&&q.x<.018&&q.y>0.&&q.y<.5){
      float t=q.y/.5;
      col=mapcol(uA.w>.5?1.-t:t,m,uv);
      col=mix(col,vec3(0.),.0);
    }
    float frame=max(seg(uv,vec2(.953,.25),vec2(.953,.75),lw),seg(uv,vec2(.975,.25),vec2(.975,.75),lw));
    for(int i=0;i<=5;i++){ float y=.25+.1*float(i); frame=max(frame,seg(uv,vec2(.940,y),vec2(.953,y),lw)); }
    hud=max(hud,frame);
  }
  col=mix(col,hc,clamp(hud,0.,1.));
  fragColor=TDOutputSwizzle(vec4(col,1.));
}
