// Final: blend sorted/source, bytebeat bit corruption bands, channel shuffle. in0 = sorted, in1 = source.
uniform vec4 uP;   // phase, loop sec, frames/loop
uniform vec4 uA;   // x sort amount, y bytebeat, z shuffle, w loopfade flag
uniform vec4 uB;   // x band density, y band height scale, z seed, w hold frames
out vec4 fragColor;
float h11(float p){ p=fract(p*.1031); p*=p+33.33; p*=p+p; return fract(p); }
float h21(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
uint bytebeat(int kind, uint t){
  if(kind==0) return ((t*((t>>5)|(t>>8)))>>(t>>16&7u))&255u;
  if(kind==1) return (t*(42u&(t>>10)))&255u;
  if(kind==2) return ((t&(t>>8))*(t>>3&t>>6))&255u;
  return ((t>>4)^(t*(t>>9&t>>13&25u)))&255u;
}
void main(){
  vec2 uv=vUV.st;
  vec2 res=uTDOutputInfo.res.zw;
  float P=uP.x;
  vec3 src=texture(sTD2DInputs[1],uv).rgb;
  vec3 srt=texture(sTD2DInputs[0],uv).rgb;
  float env=1.;
  if(uA.w>.5) env=smoothstep(0.,.12,P)*(1.-smoothstep(.88,1.,P));
  vec3 col=mix(src,srt,clamp(uA.x*env,0.,1.));
  float f=floor(floor(P*uP.z)/max(1.,uB.w));          // frame index, held
  float fs=uB.z*7.31;
  // horizontal bands
  float nb=mix(6.,60.,h11(f+fs+1.))*uB.y;
  float band=floor(uv.y*nb);
  float hb=h21(vec2(band,f+fs));
  // bytebeat corruption
  float bbAmt=uA.y;
  if(hb<bbAmt*uB.x){
    int kind=int(h11(band+f*3.+fs)*4.);
    uint t=uint(uv.x*res.x)+uint(band*977.)+uint(f)*4096u;
    uint v=bytebeat(kind,t);
    uint mask=uint(h11(band*1.7+f)*3.+1.)*0x1Fu&0xFFu;
    ivec3 ci=ivec3(clamp(col,0.,1.)*255.);
    if(h11(band*3.3+f)<.25) ci^=ivec3(int(v&mask), int((v>>1)&mask), int((v>>2)&mask)); else ci^=ivec3(int(v&mask));
    vec3 cx=vec3(ci)/255.;
    col=(h11(band+f+9.)<.3)? vec3(float(v)/255.)*vec3(1.,.9,.85)*(h11(band+f+2.)<.15?vec3(1.,.1,.08):vec3(1.)) : cx;
  }
  // channel shuffle on blocks
  float sh=uA.z;
  if(sh>0.){
    float nbx=mix(2.,8.,h11(f+fs+4.)), nby=mix(3.,14.,h11(f+fs+5.));
    vec2 id=floor(uv*vec2(nbx,nby));
    float hs=h21(id+f*1.3+fs);
    if(hs<sh*.6){
      int p=int(h21(id+f*2.1)*6.);
      if(p==0) col=col.rbg; else if(p==1) col=col.grb; else if(p==2) col=col.gbr; else if(p==3) col=col.brg; else col=col.bgr;
      // split one channel horizontally
      float off=(h21(id+f*5.)-.5)*.04*sh;
      col.r=mix(col.r,texture(sTD2DInputs[0],uv+vec2(off,0)).r,.7);
    }
  }
  fragColor=TDOutputSwizzle(vec4(col,1.));
}
