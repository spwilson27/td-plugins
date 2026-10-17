// uA: twist, bend, inflate, noise ; uB: ripple, theta(2pi*phase), noisefreq, ripplefreq ; uC: ripplecycles, noisecycles, 0,0
uniform vec4 uA, uB, uC;
float h31(vec3 p){ p = fract(p*0.3183099+0.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vnoise(vec3 x){
  vec3 i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(h31(i),h31(i+vec3(1,0,0)),f.x), mix(h31(i+vec3(0,1,0)),h31(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(h31(i+vec3(0,0,1)),h31(i+vec3(1,0,1)),f.x), mix(h31(i+vec3(0,1,1)),h31(i+vec3(1,1,1)),f.x),f.y),f.z);
}
void main(){
  const uint id = TDIndex(); if(id >= TDNumElements()) return;
  vec3 p = TDIn_P(); vec3 n = normalize(TDIn_N() + 1e-6);
  vec3 p0 = p;
  float th = uB.y;
  // twist about Y
  float a = uA.x * p.y; float ca=cos(a), sa=sin(a);
  p.xz = mat2(ca,-sa,sa,ca)*p.xz; n.xz = mat2(ca,-sa,sa,ca)*n.xz;
  // bend (xy plane rotated by angle ~ x)
  float b = uA.y * p.x; float cb=cos(b), sb=sin(b);
  p.xy = mat2(cb,-sb,sb,cb)*p.xy; n.xy = mat2(cb,-sb,sb,cb)*n.xy;
  // inflate along normal (breathing)
  p += n * uA.z * 0.5;
  // noise shell: loopable noise (point moves on a circle in noise space)
  vec3 off = vec3(cos(th*uC.y), sin(th*uC.y), 0.37*cos(th*uC.y*2.0)) * 0.9;
  float nz = vnoise(p0*uB.z + off) + 0.5*vnoise(p0*uB.z*2.1 + off*1.7 + 4.2);
  p += n * (nz - 0.75) * uA.w;
  // ripple: concentric waves from the top pole
  float d = length(p0 - vec3(0.0,1.0,0.0));
  p += n * sin(d*uB.w - th*uC.x) * uB.x * 0.25 * exp(-d*0.25);
  P[id] = p;
}
