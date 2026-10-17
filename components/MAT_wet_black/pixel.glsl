uniform vec4 uW0; // Wetness, Bump, Scale, Flow
uniform vec4 uW1; // Dripscale, Dripamt, Rough, Reflect
uniform vec4 uW2; // base color rgb
in Vertex { vec3 oP; vec3 oN; vec3 wP; vec3 wN; } vI;
out vec4 oFragColor;

// one flowing noise layer: features advect downward (-Y) by FLOWLEN world units per loop
float flowLayer(vec3 p, float t){
  vec3 q = vec3(p.x, p.y + t*2.0, p.z) * uW0.z * vec3(1.0, 0.45, 1.0);
  return fbm3(q) - 0.5;
}
float flowH(vec3 p, float ph){
  float t0 = fract(ph), t1 = fract(ph + 0.5);
  float w0 = 1.0 - abs(2.0*t0 - 1.0), w1 = 1.0 - abs(2.0*t1 - 1.0);
  // second layer offset in space so the crossfade does not pump
  return (w0*flowLayer(p, t0) + w1*flowLayer(p + vec3(5.2,1.7,3.3), t1)) * uW0.w;
}
// drips: columns along world x (set 0) and z (set 1); beads fall at integer multiples of the loop
float dripSet(float u, float y, float ph, float seed){
  float s = uW1.x*3.0;
  float cu = floor(u*s);
  float h = 0.0;
  for (int i=-1; i<=1; i++){
    float id = cu + float(i);
    float a = h11(id*1.37 + seed), b = h11(id*2.71 + seed + 4.0), c = h11(id*5.13 + seed + 9.0);
    if (a > 0.62) continue;                                   // sparse columns
    float cx = (id + 0.5 + (b-0.5)*0.5) / s;
    float dx = (u - cx) * s;
    float k = 1.0 + floor(c*3.0);                              // integer speed => loops
    float R = 3.0;                                             // wrap length in world units
    float yb = -fract(ph*k + b) * R;
    float dy = mod(y - yb + R*0.5, R) - R*0.5;                 // >0 : above bead (trail)
    float r = 0.16 + 0.10*a;
    float bead = smoothstep(r, 0.0, length(vec2(dx, dy*s*0.6)));
    float trail = smoothstep(0.075+0.03*c, 0.0, abs(dx)) * step(0.0, dy) * smoothstep(1.4, 0.0, dy) * 0.4;
    h = max(h, max(bead, trail));
  }
  return h;
}
float totalH(vec3 p){
  float ph = uP0.x;
  float h = flowH(p, ph);
  float d = max(dripSet(p.x, p.y, ph, 0.0), dripSet(p.z, p.y, ph, 17.0));
  return h + d * uW1.y;
}
void main(){
  TDCheckDiscard();
  vec3 N = normalize(vI.wN);
  vec3 P = vI.wP;
  vec3 V = normalize(camPos() - P);
  if (dot(N,V) < 0.0 && !gl_FrontFacing) N = -N;
  float e = 0.012;
  float h0 = totalH(P);
  vec3 g = vec3(totalH(P+vec3(e,0,0)) - h0, totalH(P+vec3(0,e,0)) - h0, totalH(P+vec3(0,0,e)) - h0) / e;
  g -= N*dot(g,N);
  vec3 n = normalize(N - g * 0.12 * uW0.y);
  float wet = uW0.x;
  float rough = mix(0.45, uW1.z, wet);
  vec3 R = reflect(-V, n);
  float nv = max(dot(n,V), 0.0);
  // clearcoat layer over near-black base
  float coat = mix(0.03, 0.07, wet);
  vec3 F = schlick(vec3(coat), nv);
  vec3 spec = envSample(R, rough) * F * uW1.w;
  // faint base-layer reflection (satin) and diffuse
  vec3 irr = envSample(n, 0.9);
  vec3 base = uW2.rgb * (0.2 + irr * 0.6);
  float film = smoothstep(0.0, 0.5, abs(h0)); // slightly darker/glossier where fluid pools
  vec3 col = base + spec * (1.0 + 0.4*film);
  col += envSample(reflect(-V, N), 0.35) * schlick(vec3(0.02), dot(N,V)) * 0.0;
  vec4 color = vec4(col, 1.0);
  TDAlphaTest(color.a);
  oFragColor = TDOutputSwizzle(color);
}
