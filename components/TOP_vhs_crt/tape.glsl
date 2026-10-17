// VHS tape pass. in0 = source.
uniform vec4 uP;   // phase, loop sec, frames/loop
uniform vec4 uA;   // x wobble, y jitter, z chroma bleed px, w chroma shift px
uniform vec4 uB;   // x tracking, y headswitch, z noise, w softness px
uniform vec4 uC;   // x tape on (0/1), y amount, z interlace comb, w unused
out vec4 fragColor;
const float TAU=6.2831853;
float h11(float p){ p=fract(p*.1031); p*=p+33.33; p*=p+p; return fract(p); }
float h21(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
vec3 rgb2yiq(vec3 c){ return vec3(dot(c,vec3(.299,.587,.114)),dot(c,vec3(.596,-.274,-.322)),dot(c,vec3(.211,-.523,.312))); }
vec3 yiq2rgb(vec3 y){ return vec3(y.x+.956*y.y+.621*y.z, y.x-.272*y.y-.647*y.z, y.x-1.106*y.y+1.703*y.z); }
vec3 S(vec2 uv){ return texture(sTD2DInputs[0],uv).rgb; }
void main(){
  vec2 uv=vUV.st;
  if(uC.x<.5){ fragColor=TDOutputSwizzle(vec4(S(uv),1.)); return; }
  vec2 res=uTDOutputInfo.res.zw;
  float A=uC.y, P=uP.x;
  float f=floor(P*uP.z);                 // frame index in loop (periodic hash seed)
  float row=floor(uv.y*res.y);
  float field=mod(f,2.);
  float dx=0.;
  // slow tape wobble (integer harmonics of the loop)
  dx+=uA.x*A*.006*(sin(TAU*(uv.y*3.+P*2.))+.6*sin(TAU*(uv.y*7.-P*3.)+1.3));
  // per-line jitter, changes each frame
  dx+=uA.y*A*.003*(h21(vec2(row,f))-.5)*step(.6,h21(vec2(row*.1,f+3.)));
  // interlace comb on one field
  dx+=uC.z*A*.0015*mod(row+field,2.)*sin(TAU*(P*4.+uv.y*2.));
  // tracking noise bands (3 bands moving at integer speeds)
  float band=0., bnoise=0.;
  for(int k=0;k<3;k++){
    float fk=float(k);
    float c=fract(P*(1.+fk)+fk*.37);
    float h=.03+.05*h11(fk+7.);
    float prof=smoothstep(h,0.,abs(uv.y-c));
    float tr=uB.x*A;
    dx+=prof*tr*.05*(sin(uv.y*90.+f*1.7)+ (h21(vec2(row,f+fk))-.5)*3.);
    band=max(band,prof*tr);
  }
  // head switching at bottom
  float hh=.07;
  float hs=smoothstep(hh,0.,uv.y)*uB.y*A;
  dx+=hs*hs*.12*(1.+.5*sin(TAU*P*3.))+hs*.03*(h21(vec2(row,f+11.))-.5)*4.;
  vec2 u=vec2(uv.x+dx,uv.y);
  // luma softness
  float px=1./res.x;
  vec3 y0=rgb2yiq(S(u));
  float sb=uB.w*px;
  float Y=y0.x*.5+.25*(rgb2yiq(S(u+vec2(sb,0))).x+rgb2yiq(S(u-vec2(sb,0))).x);
  // chroma bleed: wide horizontal blur of I,Q, shifted right
  vec2 IQ=vec2(0.); float ws=0.;
  float cb=max(uA.z,.001)*px*A+px;
  for(int i=-6;i<=6;i++){
    float t=float(i)/6.;
    float w=exp(-t*t*2.);
    vec3 q=rgb2yiq(S(u+vec2(t*cb*6.-uA.w*px*A,0.)));
    IQ+=q.yz*w; ws+=w;
  }
  IQ/=ws;
  vec3 col=yiq2rgb(vec3(Y,IQ));
  // noise
  float nz=uB.z*A;
  float g=h21(uv*res+f*13.17)-.5;
  col+=g*.18*nz;
  col+=(h21(vec2(row,f*1.7))-.5)*.0*nz;
  // bands: bright speckle streaks
  float sp=step(.92,h21(vec2(floor(uv.x*res.x/6.),row+f*31.)));
  col=mix(col,vec3(.85)*sp+col*.4,band*.8*step(.2,band));
  col+=band*.08;
  // head-switch noise
  float hn=smoothstep(.0,.02,hh-uv.y)*hs;
  col=mix(col,vec3(h21(vec2(floor(uv.x*res.x/3.),row+f))),hn*.6);
  fragColor=TDOutputSwizzle(vec4(max(col,0.),1.));
}
