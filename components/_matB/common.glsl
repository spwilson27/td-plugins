// ---- matB common: noise, studio environment, PBR-ish shading ----
#define PI 3.14159265359
#define TAU 6.28318530718
uniform vec4 uEnv; // x = env rotation (rad), y = env intensity, z = loop phase 0..1

in Vtx {
  vec3 wP; vec3 wN; vec3 oP; vec3 oN; vec3 cam;
  vec3 ax; vec3 ay; vec3 az;   // object axes in world space
  float sh;                    // shell fraction (velvet) / 0
} vv;

float sat(float x){ return clamp(x,0.,1.); }
vec3 sat3(vec3 x){ return clamp(x,0.,1.); }

float hash13(vec3 p3){ p3 = fract(p3*.1031); p3 += dot(p3,p3.zyx+31.32); return fract((p3.x+p3.y)*p3.z); }
vec3 hash33(vec3 p3){ p3 = fract(p3*vec3(.1031,.1030,.0973)); p3 += dot(p3,p3.yxz+33.33); return fract((p3.xxy+p3.yxx)*p3.zyx); }

float vnoise(vec3 p){
  vec3 i = floor(p), f = fract(p);
  vec3 u = f*f*f*(f*(f*6.-15.)+10.);
  float a=hash13(i), b=hash13(i+vec3(1,0,0)), c=hash13(i+vec3(0,1,0)), d=hash13(i+vec3(1,1,0));
  float e=hash13(i+vec3(0,0,1)), g=hash13(i+vec3(1,0,1)), h=hash13(i+vec3(0,1,1)), k=hash13(i+vec3(1,1,1));
  return mix(mix(mix(a,b,u.x),mix(c,d,u.x),u.y), mix(mix(e,g,u.x),mix(h,k,u.x),u.y), u.z);
}
float fbm(vec3 p){
  float a=.5, s=0.;
  for(int i=0;i<4;i++){ s += a*vnoise(p); p = p*2.03 + vec3(1.7,9.2,3.1); a *= .5; }
  return s/0.9375;
}
float fbm2(vec3 p){ // 2 octaves, cheap
  return (vnoise(p)*.6 + vnoise(p*2.1+vec3(3.1,1.7,5.3))*.4);
}
// periodic circular path through noise space: loops when ph goes 0..1 (k = integer revs)
vec3 loopOff(float ph, float k, float rad){ float a = TAU*ph*k; return rad*vec3(cos(a), sin(a), cos(a)*sin(a)*2.0); }

// voronoi: returns (F1, F2). Static.
vec2 voro(vec3 p){
  vec3 i = floor(p), f = fract(p); float d1=9., d2=9.;
  for(int z=-1;z<=1;z++) for(int y=-1;y<=1;y++) for(int x=-1;x<=1;x++){
    vec3 g = vec3(x,y,z);
    vec3 o = hash33(i+g);
    float d = length(g + o - f);
    if(d<d1){ d2=d1; d1=d; } else if(d<d2){ d2=d; }
  }
  return vec2(d1,d2);
}
// voronoi with feature points orbiting (periodic in ph, 1 rev per loop)
vec2 voroA(vec3 p, float ph){
  vec3 i = floor(p), f = fract(p); float d1=9., d2=9.;
  for(int z=-1;z<=1;z++) for(int y=-1;y<=1;y++) for(int x=-1;x<=1;x++){
    vec3 g = vec3(x,y,z);
    vec3 h = hash33(i+g);
    vec3 o = 0.5 + 0.38*sin(TAU*(ph + h*vec3(1.0,1.0,1.0)) + h.zxy*TAU);
    float d = length(g + o - f);
    if(d<d1){ d2=d1; d1=d; } else if(d<d2){ d2=d; }
  }
  return vec2(d1,d2);
}

// ---- studio environment (also the "lights"): key, fill, rim, strip ----
mat3 envRot(){ float c=cos(uEnv.x), s=sin(uEnv.x); return mat3(c,0,-s, 0,1,0, s,0,c); }
const vec3 L0 = vec3(-0.5145,0.6001,0.6001);   // key (front-left-top)
const vec3 L1 = vec3(0.8,0.1,0.55);             // fill (right)
const vec3 L2 = vec3(0.25,0.35,-0.9);           // rim (back)
const vec3 L3 = vec3(-0.85,0.15,-0.5);          // rim2 (back-left)
const vec3 C0 = vec3(1.0,0.95,0.88)*3.2;
const vec3 C1 = vec3(0.55,0.66,0.95)*0.9;
const vec3 C2 = vec3(1.0,1.0,1.0)*4.0;
const vec3 C3 = vec3(0.9,0.6,0.5)*1.6;
float lobe(vec3 d, vec3 L, float w){ return exp((dot(d,L)-1.0)/w); }
vec3 studioEnv(vec3 d, float rough){
  d = envRot()*d;
  float w = 0.012 + rough*rough*0.85;
  float amp = 0.07/(w+0.07);
  vec3 c = mix(vec3(0.006,0.006,0.008), vec3(0.035,0.037,0.045), smoothstep(-1.,1.,d.y));
  c += C0*lobe(d,L0,w*1.6)*amp + C1*lobe(d,L1,w*2.0)*amp + C2*lobe(d,L2,w*1.2)*amp + C3*lobe(d,L3,w*1.4)*amp;
  // overhead strip + horizon strip for readable reflections
  float sw = 0.04 + rough*0.5;
  c += vec3(0.9)*0.6*exp(-pow((d.y-0.82)/sw,2.0))*smoothstep(-0.2,0.6,d.z)*0.7*amp*2.0;
  c += vec3(0.8,0.85,1.0)*0.35*exp(-pow((d.y-0.12)/(sw*0.8),2.0))*smoothstep(0.1,0.9,d.z+0.3*d.x)*amp*2.0;
  return c*uEnv.y;
}
vec3 diffuseLight(vec3 N, float wrap){
  N = envRot()*N;
  vec3 s = vec3(0.025,0.027,0.035)*(0.6+0.4*N.y);
  s += C0*sat((dot(N,L0)+wrap)/(1.+wrap))*0.30;
  s += C1*sat((dot(N,L1)+wrap)/(1.+wrap))*0.30;
  s += C2*sat((dot(N,L2)+wrap)/(1.+wrap))*0.22;
  s += C3*sat((dot(N,L3)+wrap)/(1.+wrap))*0.25;
  return s*uEnv.y*0.55;
}
vec3 envBRDF(vec3 F0, float rough, float NdV){
  const vec4 c0 = vec4(-1,-0.0275,-0.572,0.022), c1 = vec4(1,0.0425,1.04,-0.04);
  vec4 r = rough*c0 + c1; float a004 = min(r.x*r.x, exp2(-9.28*NdV))*r.x + r.y;
  vec2 AB = vec2(-1.04,1.04)*a004 + r.zw; return F0*AB.x + AB.y;
}
vec3 shadePBR(vec3 N, vec3 V, vec3 albedo, float metal, float rough, float ao){
  vec3 F0 = mix(vec3(0.04), albedo, metal);
  float NdV = sat(dot(N,V));
  vec3 diff = albedo*(1.0-metal)*diffuseLight(N,0.0)*ao;
  vec3 spec = studioEnv(reflect(-V,N), rough)*envBRDF(F0,rough,NdV)*mix(1.0,ao,0.7);
  return diff + spec;
}
// perturb world normal with an object-space height gradient
vec3 bumpN(vec3 N, vec3 gradObj, float k){
  vec3 g = gradObj.x*normalize(vv.ax) + gradObj.y*normalize(vv.ay) + gradObj.z*normalize(vv.az);
  g -= N*dot(g,N);
  return normalize(N - k*g);
}
// triplanar-ish object position helpers
vec3 objPos(){ return vv.oP; }
// screen-space derivative bump (Mikkelsen): h = scalar height (world-space units), k = strength
vec3 bumpDeriv(vec3 N, float h, float k){
  vec3 dpdx = dFdx(vv.wP), dpdy = dFdy(vv.wP);
  vec3 R1 = cross(dpdy, N), R2 = cross(N, dpdx);
  float det = dot(dpdx, R1);
  vec3 grad = sign(det)*(dFdx(h)*R1 + dFdy(h)*R2);
  return normalize(abs(det)*N - k*grad);
}
