uniform vec4 uC0; // Facetmode(0 voronoi,1 flat), Facetscale, Facetstrength, Ior
uniform vec4 uC1; // Dispersion, Inner, Sparkle, Sparklescale
uniform vec4 uC2; // tint rgb, Tintamt
uniform vec4 uC3; // Reflect, Absorb, Twinkle, 0
in Vertex { vec3 oP; vec3 oN; vec3 wP; vec3 wN; } vI;
out vec4 oFragColor;

// 3D Worley: returns (F1, cell hash, F2-F1) ; cell id via out param
vec3 worley(vec3 p, out vec3 cid){
  vec3 ip = floor(p), fp = fract(p);
  float d1 = 9.0, d2 = 9.0; vec3 best = vec3(0.0);
  for (int z=-1; z<=1; z++) for (int y=-1; y<=1; y++) for (int x=-1; x<=1; x++){
    vec3 g = vec3(x,y,z);
    vec3 r = h33(ip + g);
    vec3 o = g + 0.15 + 0.7*r - fp;
    float d = dot(o,o);
    if (d < d1){ d2 = d1; d1 = d; best = ip + g; }
    else if (d < d2) d2 = d;
  }
  cid = best;
  return vec3(sqrt(d1), h13(best), sqrt(d2) - sqrt(d1));
}
vec3 rvec(vec3 id){ return normalize(h33(id) * 2.0 - 1.0); }

void main(){
  TDCheckDiscard();
  vec3 N = normalize(vI.wN);
  vec3 P = vI.wP;
  vec3 V = normalize(camPos() - P);
  if (dot(N,V) < 0.0 && !gl_FrontFacing) N = -N;
  vec3 I = -V;
  // ---- facet normal ----
  vec3 cid;
  vec3 w = worley(vI.oP * uC0.y, cid);
  vec3 nF;
  if (uC0.x < 0.5){
    // voronoi facets: every cell gets a constant tilted normal (object-space tilt -> rotated to world via N frame)
    vec3 t = rvec(cid);
    nF = normalize(N + t * uC0.z);
  } else {
    vec3 fn = normalize(cross(dFdx(P), dFdy(P)));
    if (dot(fn, V) < 0.0) fn = -fn;
    nF = normalize(mix(N, fn, clamp(uC0.z, 0.0, 1.0)));
  }
  nF = normalize(mix(nF, N, 0.2) + (vI.oP - floor(vI.oP*uC0.y)/uC0.y) * 0.0);
  float nv = max(dot(nF, V), 0.0);
  // ---- refraction with per-channel IOR, second (back) interface = another random facet ----
  vec3 nB = -normalize(mix(nF, rvec(cid + 7.31), uC1.y*0.8));
  vec3 col = vec3(0.0);
  float iors[3];
  iors[0] = uC0.w - uC1.x; iors[1] = uC0.w; iors[2] = uC0.w + uC1.x;
  vec3 T0 = vec3(0.0);
  for (int c=0; c<3; c++){
    float eta = 1.0 / iors[c];
    vec3 T1 = refract(I, nF, eta);
    if (dot(T1,T1) < 1e-6) T1 = reflect(I, nF);
    vec3 T2 = refract(T1, nB, iors[c]);          // exit
    if (dot(T2,T2) < 1e-6) T2 = reflect(T1, nB);  // internal reflection
    if (c == 1) T0 = T1;
    float e = envSample(normalize(T2), 0.06)[c];
    col[c] = e;
  }
  // absorption / tint: thicker (grazing) path absorbs more
  float path = 0.4 + 1.6*(1.0 - nv);
  vec3 absorb = exp(-(1.0 - uC2.rgb) * uC3.y * path * uC2.a);
  col *= absorb;
  // ---- surface reflection ----
  vec3 R = reflect(I, nF);
  float F = schlick(vec3(0.04), nv).r;
  col += envSample(R, 0.04) * F * uC3.x * 2.0;
  // ---- internal sparkle: tiny flakes with parallax by refracted dir, twinkle loops in phase ----
  vec3 sp = (vI.oP + T0 * 0.25) * uC1.w;
  vec3 sid = floor(sp);
  float sh = h13(sid);
  vec3 sn = rvec(sid + 3.7);
  float tw = 0.5 + 0.5*sin(TAU*(uP0.x * (1.0 + floor(sh*3.0)) + sh));
  float flake = step(0.82, h13(sid + 11.0));
  vec3 Rs = reflect(I, normalize(nF + sn * 0.9));
  float spec = pow(max(dot(Rs, normalize(vec3(0.5,0.8,0.6))), 0.0), 40.0) + pow(max(dot(Rs, normalize(vec3(-0.7,0.3,0.5))), 0.0), 40.0);
  float ctr = length(fract(sp) - 0.5);
  float spark = flake * smoothstep(0.35, 0.0, ctr) * (spec * 6.0 + 0.4) * mix(1.0, tw, uC3.z);
  col += spark * uC1.z * vec3(1.0, 0.97, 0.92) * (0.3 + 0.7 * uC2.rgb);
  // facet edge glint
  col += vec3(0.8,0.9,1.0) * smoothstep(0.05, 0.0, w.z) * 0.15 * uC3.x;
  vec4 color = vec4(col, 1.0);
  TDAlphaTest(color.a);
  oFragColor = TDOutputSwizzle(color);
}
