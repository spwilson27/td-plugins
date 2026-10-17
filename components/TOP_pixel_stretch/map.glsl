// pixel_stretch pass A: 2048x1 column map. per column(band): start position t where luminance crosses the threshold + the colour there
uniform vec4 uA; // ph, dir, threshold, animate
uniform vec4 uB; // noise, invert, unused, unused
out vec4 fragColor;
#define TAU 6.28318530718
float h31(vec3 p){ p=fract(p*vec3(.1031,.1030,.0973)); p+=dot(p,p.yxz+33.33); return fract((p.x+p.y)*p.z); }
float vn3(vec3 p){ vec3 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(mix(h31(i),h31(i+vec3(1,0,0)),f.x),mix(h31(i+vec3(0,1,0)),h31(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(h31(i+vec3(0,0,1)),h31(i+vec3(1,0,1)),f.x),mix(h31(i+vec3(0,1,1)),h31(i+vec3(1,1,1)),f.x),f.y),f.z); }
vec2 toUV(float a,float t,int dir){
  if(dir==0) return vec2(a,1.-t);
  if(dir==1) return vec2(a,t);
  if(dir==2) return vec2(1.-t,a);
  return vec2(t,a);
}
void main(){
  float a=(floor(gl_FragCoord.x)+.5)/2048.;
  int dir=int(uA.y+.5);
  float th=uA.x*TAU;
  // threshold: base + loop-periodic animation + per-column noise on a circular noise path
  float thr=uA.z+uA.w*sin(th)*.5;
  float nz=vn3(vec3(a*70.,cos(th)*1.5,sin(th)*1.5))*2.-1.;
  thr+=uB.x*nz*.45;
  vec4 outv=vec4(2.,0.,0.,0.);
  const int STEPS=200;
  for(int k=0;k<STEPS;k++){
    float t=(float(k)+.5)/float(STEPS);
    vec3 c=texture(sTD2DInputs[0],toUV(a,t,dir)).rgb;
    float l=dot(c,vec3(.299,.587,.114));
    bool cross=uB.y>.5? (l<thr) : (l>thr);
    if(cross){ outv=vec4(t,c); break; }
  }
  fragColor=outv;
}
