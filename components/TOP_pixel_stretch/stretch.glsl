// pixel_stretch pass B: repeat/stretch the crossing pixel along the direction with fading streaks + grain
uniform vec4 uA; // ph, dir, length, bandwidth px
uniform vec4 uB; // grain, mix, revert, streak
uniform vec4 uC; // seed (frames/loop), unused
out vec4 fragColor;
#define TAU 6.28318530718
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float vn1(float x,float s){ float i=floor(x),f=fract(x); f=f*f*(3.-2.*f); return mix(h21(vec2(i,s)),h21(vec2(i+1.,s)),f); }
void main(){
  vec2 res=uTDOutputInfo.res.zw;
  vec2 uv=vUV.st;
  int dir=int(uA.y+.5);
  float a,t;
  if(dir==0){ a=uv.x; t=1.-uv.y; } else if(dir==1){ a=uv.x; t=uv.y; }
  else if(dir==2){ a=uv.y; t=1.-uv.x; } else { a=uv.y; t=uv.x; }
  float resA=dir<2?res.x:res.y, resT=dir<2?res.y:res.x;
  float bw=max(uA.w,1.);
  float bi=floor(a*resA/bw);
  float aq=(bi+.5)*bw/resA;
  vec4 m=texelFetch(sTD2DInputs[1],ivec2(int(aq*2048.),0),0);
  vec3 orig=texture(sTD2DInputs[0],uv).rgb;
  float th=uA.x*TAU;
  vec3 col=orig*uB.z;
  float ts=m.x;
  if(ts<1.5){
    float d=t-ts;                                   // distance (0..1) past the start pixel
    if(d>=0.){
      // per-band streak variation: length multiplier + fine fibre noise along the stripe axis
      float fib=vn1(a*resA*.5,3.)*.6+vn1(a*resA*1.7,9.)*.4;
      float band=h21(vec2(bi,7.));
      float L=uA.z*(.35+1.3*mix(band,fib,uB.w));
      float f=exp(-d/max(L,1e-3)*2.2);
      // slow wobble in the streak intensity along travel, loop-periodic
      float wob=.8+.2*sin(d*60.*(.5+band)+th*floor(1.+band*3.)+band*TAU);
      vec3 stuck=m.yzw*wob;
      // slight stretch-resampling feel: mix toward the live image far from the edge
      col=mix(orig*uB.z,stuck,f);
      col+=stuck*.15*exp(-d*40.);                   // bright edge at crossing
    }
  }
  // grain (loop-periodic seed: frame index modulo uC.x)
  float fr=mod(floor(uA.x*uC.x),uC.x);
  float gr=h21(uv*res+fr*17.31)-.5;
  col+=gr*uB.x*.35*(0.4+dot(col,vec3(.33)))+gr*uB.x*.03;
  col=mix(orig,col,uB.y);
  fragColor=TDOutputSwizzle(vec4(max(col,0.),1.));
}
