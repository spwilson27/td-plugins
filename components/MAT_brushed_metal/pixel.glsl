uniform vec4 uB0; // mode, Brushscale, Streakamt, Roughalong
uniform vec4 uB1; // Roughacross, Anodize, Heightmix, Tintrange
uniform vec4 uB2; // Tintoffset, Tintanim, Reflect, Aniso samples spread
uniform vec4 uB3; // base rgb, 0
in Vertex { vec3 oP; vec3 oN; vec3 wP; vec3 wN; vec3 wT; vec3 oT; } vI;
out vec4 oFragColor;

// titanium anodizing palette: gold -> magenta -> violet -> blue -> teal -> straw gold
vec3 heat(float t){
  t = fract(t) * 6.0;
  vec3 c0 = vec3(0.85,0.55,0.12), c1 = vec3(0.75,0.12,0.40), c2 = vec3(0.22,0.06,0.70);
  vec3 c3 = vec3(0.04,0.22,0.90), c4 = vec3(0.10,0.62,0.62), c5 = vec3(0.75,0.62,0.12);
  if (t < 1.0) return mix(c0,c1,smoothstep(0.,1.,t));
  if (t < 2.0) return mix(c1,c2,smoothstep(0.,1.,t-1.));
  if (t < 3.0) return mix(c2,c3,smoothstep(0.,1.,t-2.));
  if (t < 4.0) return mix(c3,c4,smoothstep(0.,1.,t-3.));
  if (t < 5.0) return mix(c4,c5,smoothstep(0.,1.,t-4.));
  return mix(c5,c0,smoothstep(0.,1.,t-5.));
}
void main(){
  TDCheckDiscard();
  vec3 N = normalize(vI.wN);
  vec3 P = vI.wP;
  vec3 V = normalize(camPos() - P);
  if (dot(N,V) < 0.0 && !gl_FrontFacing) N = -N;
  vec3 T = normalize(vI.wT - N*dot(vI.wT,N));
  vec3 B = cross(N, T);
  // streak noise: high frequency across the brush direction, very long along it (object space frame)
  vec3 oB = cross(normalize(vI.oN), vI.oT);
  float sf = uB0.y;
  float s1 = vnoise(vec3(dot(vI.oP,oB)*sf, dot(vI.oP,vI.oT)*sf*0.03, 0.37));
  float s2 = vnoise(vec3(dot(vI.oP,oB)*sf*2.7, dot(vI.oP,vI.oT)*sf*0.05, 4.1));
  float streak = s1*0.6 + s2*0.4;
  vec3 n = normalize(N + B * (streak-0.5) * uB0.z * 0.5);
  float nv = max(dot(n,V), 0.0);
  vec3 R = reflect(-V, n);
  // anisotropic highlight: smear env lookup across the brush (along B); little smear along T
  float ra = uB0.w, rc = uB1.x;
  vec3 acc = vec3(0.0); float wsum = 0.0;
  for (int i=-6; i<=6; i++){
    float s = float(i)/6.0;
    float wgt = exp(-s*s*1.8);
    vec3 d = normalize(R + B * s * rc * 1.6 + T * (s*0.0));
    acc += envSample(d, ra*0.5) * wgt; wsum += wgt;
  }
  vec3 env = acc / wsum;
  // anodize colour: oxide thickness varies by view angle and object-space height
  float tv = mix(1.0 - nv, vI.oP.y*0.5 + 0.5, uB1.z);
  float tt = uB2.x + uB1.w * tv + 0.04*(streak-0.5)*uB1.w + uB2.y*sin(TAU*uP0.x);
  vec3 pal = heat(tt);
  vec3 base = uB3.rgb;
  vec3 f0 = mix(base, pal * 1.05, uB1.y);
  vec3 F = mix(schlick(f0, nv), f0 + (1.0-f0)*pow(1.0-nv,5.0)*0.35, uB1.y);
  F *= 0.72 + 0.56*streak;
  vec3 col = env * F * uB2.z;
  // small diffuse floor so unlit sides are not pitch black
  col += f0 * envSample(n, 1.0) * 0.12;
  vec4 color = vec4(col, 1.0);
  TDAlphaTest(color.a);
  oFragColor = TDOutputSwizzle(color);
}
