// straight unit tube (y in -0.5..0.5, radius .5) -> noise-driven curved tentacle. Template root pos in Color.rgb
// uA: length, wiggle, thick, taper ; uB: theta, noisefreq, pulseamt, pulsefreq
// uC: grow, tipmin, wavefreq, waveamp ; uD: rootradius, noisecycles, wavecycles, 0
uniform vec4 uA, uB, uC, uD;
float h31(vec3 p){ p = fract(p*0.3183099+0.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vn(vec3 x){
  vec3 i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(h31(i),h31(i+vec3(1,0,0)),f.x), mix(h31(i+vec3(0,1,0)),h31(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(h31(i+vec3(0,0,1)),h31(i+vec3(1,0,1)),f.x), mix(h31(i+vec3(0,1,1)),h31(i+vec3(1,1,1)),f.x),f.y),f.z);
}
vec3 vn3(vec3 q){ return vec3(vn(q), vn(q+vec3(17.1,3.7,9.2)), vn(q+vec3(5.3,31.1,13.9))) - 0.5; }
vec3 g_dir, g_p1, g_p2, g_root; float g_seed;
vec3 spine(float s){          // s in 0..1 along the (grown) tentacle
  float th = uB.x;
  vec3 off = vec3(cos(th*uD.y), sin(th*uD.y), 0.5*cos(2.0*th*uD.y))*0.8;
  float L = uA.x*uC.x;
  float u = s;
  vec3 q = g_dir*2.3 + vec3(0.0, u*uB.y, 0.0) + off + g_seed*3.0;
  vec3 d = vn3(q)*2.0 * uA.y * L * smoothstep(0.0,0.5,u) * (0.4+0.6*u);
  float wph = 6.2831853*(uC.z*u - uD.z*uB.x/6.2831853) + g_seed*6.28;
  vec3 sway = (g_p1*sin(wph) + g_p2*cos(wph+1.3+u*2.0))*uC.w*L*u*u;
  return g_root + g_dir*L*u + d + sway;
}
void main(){
  const uint id = TDIndex(); if(id >= TDNumElements()) return;
  vec3 lp = TDIn_P();
  g_root = TDIn_Color().rgb;
  g_dir = normalize(g_root + 1e-5);
  g_seed = h31(g_root*7.7 + 3.1);
  g_p1 = normalize(cross(g_dir, abs(g_dir.y)<0.9 ? vec3(0,1,0) : vec3(1,0,0)));
  g_p2 = cross(g_dir, g_p1);
  float u = clamp(lp.y + 0.5, 0.0, 1.0);
  float ang = atan(lp.z, lp.x);
  vec3 c0 = spine(u);
  vec3 T = normalize(spine(min(u+0.01,1.0)) - spine(max(u-0.01,0.0)) + 1e-6);
  // parallel-ish transport: frame from base direction projected perpendicular to T
  vec3 N = normalize(g_p1 - T*dot(g_p1,T));
  vec3 B = cross(T, N);
  float r = uA.z * pow(1.0-u, uA.w) + uC.y*uA.z*(1.0-u);
  r *= 1.0 + uB.z*sin(6.2831853*(uB.w*u*0.5 - uD.z*uB.x/6.2831853*1.0) + g_seed*6.0)*smoothstep(0.0,0.3,u);
  r *= smoothstep(0.0, 0.01, uC.x);
  vec3 p = c0 + (cos(ang)*N + sin(ang)*B)*r*(length(lp.xz)*2.0);
  P[id] = p;
}
