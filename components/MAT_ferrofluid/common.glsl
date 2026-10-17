// ---- ferrofluid shared (vertex + pixel) ----
uniform vec4 uF0; // Spikescale, Height, Sharp, Regular
uniform vec4 uF1; // Baseline, Modulation, Pull, Reach
uniform vec4 uF2; // attractor xyz (world), Lean
uniform vec4 uF3; // Wobble, Varia, Radius, 0
vec3 fh33(vec3 p3){ p3=fract(p3*vec3(.1031,.1030,.0973)); p3+=dot(p3,p3.yxz+33.33); return fract((p3.xxy+p3.yxx)*p3.zyx); }
float fh13(vec3 p3){ p3=fract(p3*.1031); p3+=dot(p3,p3.zyx+31.32); return fract((p3.x+p3.y)*p3.z); }
// spike profile at object-space point p: x = shape 0..1 (1 at tip), y = cell hash
vec2 spikeShape(vec3 p){
  vec3 q = p * uF0.x;
  vec3 ip = floor(q), fp = fract(q);
  float d1 = 9.0; vec3 best = vec3(0.0);
  float jit = 1.0 - uF0.w * 0.95;                         // Regular=1 -> near-regular lattice
  for (int z=-1; z<=1; z++) for (int y=-1; y<=1; y++) for (int x=-1; x<=1; x++){
    vec3 g = vec3(x,y,z);
    vec3 o = g + 0.5 + (fh33(ip+g)-0.5)*jit - fp;
    float d = dot(o,o);
    if (d < d1){ d1 = d; best = ip+g; }
  }
  float d = sqrt(d1);
  float s = pow(clamp(1.0 - d/0.62, 0.0, 1.0), uF0.z);
  return vec2(s, fh13(best));
}
// field strength at a world-space position (attractor pull + baseline + modulation)
float fieldAmp(vec3 wp){
  float dd = length(wp - uF2.xyz);
  float pull = uF1.z * exp(-dd*dd / (uF1.w*uF1.w + 1e-4));
  return clamp(uF1.x + uF1.y + pull, 0.0, 2.5);
}
