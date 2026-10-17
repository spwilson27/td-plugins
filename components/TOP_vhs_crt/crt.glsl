// CRT display pass. in0 = tape output.
uniform vec4 uP;   // time in 8 s units (unwrapped), 8, 240 (30 hash frames/s)
uniform vec4 uA;   // x curvature, y scanlines strength, z mask strength, w glow
uniform vec4 uB;   // x vignette, y flicker, z interlace, w scan line count
uniform vec4 uC;   // x crt on, y amount
out vec4 fragColor;
const float TAU=6.2831853;
vec3 S(vec2 uv){ return texture(sTD2DInputs[0],uv).rgb; }
void main(){
  vec2 uv=vUV.st;
  if(uC.x<.5){ fragColor=TDOutputSwizzle(vec4(S(uv),1.)); return; }
  vec2 res=uTDOutputInfo.res.zw;
  float P=uP.x, A=uC.y;
  float asp=res.x/res.y;
  vec2 p=uv*2.-1.;
  float k=uA.x*A;
  p*=1.+k*.12*vec2(p.y*p.y,p.x*p.x)+k*.04*dot(p,p);
  p/=1.+k*.07;
  vec2 q=p*.5+.5;
  // rounded-corner screen mask
  vec2 e=abs(p)-vec2(1.)+.05;
  float inside=1.-smoothstep(-.01,.02,length(max(e,0.))-.05);
  inside*=step(abs(p.x),1.02)*step(abs(p.y),1.02);
  vec3 c=S(q);
  // glow (cheap 2-ring blur)
  vec3 b=vec3(0.);
  for(int i=0;i<8;i++){
    float a=TAU*float(i)/8.;
    b+=S(q+vec2(cos(a),sin(a))*vec2(5.,5.)/res)*.6+S(q+vec2(cos(a),sin(a))*vec2(12.,12.)/res)*.4;
  }
  b/=8.;
  c+=b*uA.w*A*.8;
  // scanlines + interlace
  float lines=uB.w;
  float li=q.y*lines;
  float field=mod(floor(P*uP.z),2.);
  float sl=.5+.5*cos(TAU*li);
  float lit=mod(floor(li),2.)==field?1.:1.-uB.z*.55;
  c*=mix(1.,mix(.35,1.,sl)*lit,clamp(uA.y*A,0.,1.2));
  c*=1.+uA.y*A*.35;
  // shadow mask (RGB triads + slot rows)
  float xm=mod(floor(q.x*res.x),3.);
  vec3 m=vec3(xm<.5?1.:.35, (xm>.5&&xm<1.5)?1.:.35, xm>1.5?1.:.35);
  float rowm=mod(floor(q.y*res.y/2.),2.);
  m*=mix(1.,.8,rowm*step(1.5,xm));
  c*=mix(vec3(1.),m*1.5,uA.z*A);
  // vignette
  vec2 vv=q*(1.-q);
  float vig=pow(clamp(vv.x*vv.y*16.,0.,1.),uB.x*A*.6+.001);
  c*=mix(1.,vig,clamp(uB.x*A,0.,1.));
  // flicker + hum bar (integer cycles per loop)
  float fk=floor(uP.y*50.+.5);
  c*=1.+uB.y*A*.04*sin(TAU*P*fk);
  c*=1.-uB.y*A*.10*smoothstep(.12,0.,abs(fract(q.y-P*2.)-.5)-.0)*.3;
  fragColor=TDOutputSwizzle(vec4(c*inside,1.));
}
