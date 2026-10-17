// uA: dissolve(0-1), wavemode(0 plane,1 sphere,2 radial), scatter, jitter
// uB: theta(2pi*phase), noisefreq, edgewidth, drift
// uC: shape(0 sphere,1 torus,2 blob,3 image), depth, bright, noisecycles
// uD: axis xyz, flip luma
// uE: wave center/lighting etc (cx,cy,cz, edgeglow)
uniform vec4 uA, uB, uC, uD, uE, uF;
float hid(uint i, float k){ return fract(sin(float(i)*12.9898+k*78.233)*43758.5453); }
float h31(vec3 p){ p = fract(p*0.3183099+0.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vn(vec3 x){
  vec3 i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(h31(i),h31(i+vec3(1,0,0)),f.x), mix(h31(i+vec3(0,1,0)),h31(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(h31(i+vec3(0,0,1)),h31(i+vec3(1,0,1)),f.x), mix(h31(i+vec3(0,1,1)),h31(i+vec3(1,1,1)),f.x),f.y),f.z);
}
vec3 pot(vec3 p, vec3 off){ return vec3(vn(p+off), vn(p+vec3(31.4,7.1,13.7)+off), vn(p+vec3(11.3,47.9,3.1)+off)); }
vec3 curl(vec3 p, vec3 off){
  const float e = 0.07;
  vec3 dx = pot(p+vec3(e,0,0),off) - pot(p-vec3(e,0,0),off);
  vec3 dy = pot(p+vec3(0,e,0),off) - pot(p-vec3(0,e,0),off);
  vec3 dz = pot(p+vec3(0,0,e),off) - pot(p-vec3(0,0,e),off);
  return vec3(dy.z-dz.y, dz.x-dx.z, dx.y-dy.x)/(2.0*e);
}
void main(){
  const uint id = TDIndex(); if(id >= TDNumElements()) return;
  vec3 p0 = TDIn_P(); vec3 n = normalize(TDIn_N()+1e-6);
  float lum = 1.0;
  int shape = int(uC.x+0.5);
  if(shape==3){
    vec2 uv = p0.xy*0.5+0.5;
    vec3 t = texture(uTex, uv).rgb;
    float l = dot(t, vec3(0.299,0.587,0.114)); if(uD.w>0.5) l = 1.0-l;
    lum = l;
    p0 = vec3(p0.xy*1.2, (l-0.5)*uC.y);
    n = vec3(0.0,0.0,1.0);
  } else if(shape==2){
    // head-ish blob: elongated, lumpy, nose bump
    p0.y *= 1.25; p0.x *= 0.85;
    float nb = exp(-dot(p0-vec3(0,0.05,0.9),p0-vec3(0,0.05,0.9))*14.0);
    p0 += n*(vn(p0*2.2)*0.28 - 0.14) + vec3(0,0,1)*nb*0.35;
  }
  // wave coordinate t in 0..1
  float R = 1.5;
  float tw;
  vec3 ax = normalize(uD.xyz + 1e-5);
  float th = uB.x;
  vec3 noff = vec3(cos(th*uC.w), sin(th*uC.w), 0.4*cos(th*uC.w*2.0))*0.8;
  float jit = (vn(p0*2.5 + noff) - 0.5) * uA.w;
  int mode = int(uA.y+0.5);
  if(mode==0){ tw = dot(p0, ax)/R*0.5+0.5; }
  else if(mode==1){ vec3 c = vec3(cos(th), 0.2, sin(th))*0.7 * uE.xyz; tw = length(p0-c)/(R*1.6); }
  else { tw = length(p0 - ax*dot(p0,ax))/R; }
  tw += jit;
  float W = max(uB.z, 0.02);
  float e = smoothstep(0.0, 1.0, (uA.x*(1.0+W+uA.w) - tw)/W);
  // scatter
  vec3 cv = curl(p0*uB.y + noff, noff*0.5);
  vec3 disp = cv*uA.z*e*e*0.5 + ax*uB.w*e*e + normalize(p0+1e-5)*e*0.15*uA.z;
  vec3 rnd = vec3(hid(id,1.0), hid(id,2.0), hid(id,3.0)) - 0.5;
  disp += rnd*e*uA.z*0.9*(0.3+e);
  vec3 p = p0 + disp;
  float edge = e*(1.0-e)*4.0;
  vec3 L = normalize(vec3(0.5,0.8,0.6));
  float shade = (shape==3) ? (0.25+0.75*lum) : (0.3+0.7*max(dot(n,L),0.0)+0.2*pow(1.0-abs(n.z),2.0));
  float a = 1.0 - smoothstep(0.82, 1.0, e);
  vec3 col = vec3(shade) * uC.z * (1.0 + edge*uE.w);
  P[id] = p;
  Color[id] = vec4(col, a);
  PointScale[id] = uF.x*(0.6+0.8*hid(id,5.0))*(1.0 - 0.5*e);
}
