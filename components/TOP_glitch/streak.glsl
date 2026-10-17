// Approximate pixel-sort streaks along an axis (the one sub-effect that stays GLSL: it needs a per-pixel scan loop).
// in0 = image. Runs of pixels brighter than the threshold are smeared along the lane toward their brightest pixel.
uniform vec4 uS;   // x pixel sort amount (already x Amount), y threshold, z axis (0 horizontal, 1 vertical), w beat
out vec4 fragColor;
float hash21(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
float luma(vec3 c){ return dot(c,vec3(.299,.587,.114)); }
vec3 S(vec2 uv){ return texture(sTD2DInputs[0],uv).rgb; }

void main(){
  vec2 uv=vUV.st;
  vec2 px=uTDOutputInfo.res.xy;
  float beat=uS.w, pa=uS.x, thr=uS.y;
  vec3 c=S(uv);
  vec2 dir=uS.z<.5?vec2(px.x,0.):vec2(0.,px.y);
  float lane=uS.z<.5?floor(uv.y*180.):floor(uv.x*320.);
  float maxN=6.+floor(hash21(vec2(lane,beat))*42.);
  float l0=luma(c);
  if(l0>thr && hash21(vec2(lane,beat+2.))<pa*1.4){
    vec3 best=c; float bl=l0; int n=0;
    vec3 start=c;
    for(int i=1;i<=48;i++){
      if(float(i)>maxN) break;
      vec3 s=S(uv-dir*float(i)*3.);
      float ls=luma(s);
      if(ls<=thr) break;
      start=s; n=i;
      if(ls>bl){ bl=ls; best=s; }
    }
    float t=float(n)/maxN;
    c=mix(c,mix(start,best,smoothstep(0.,1.,t)),clamp(pa*1.5,0.,1.));
  }
  fragColor=TDOutputSwizzle(vec4(c,texture(sTD2DInputs[0],uv).a));
}
