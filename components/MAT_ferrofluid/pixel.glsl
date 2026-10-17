in Vertex { vec3 oP; vec3 oN; vec3 wP; vec3 wN; vec3 wP0; float hgt; vec3 wT1; } vI;
uniform vec4 uF4; // base rgb, Reflectivity
uniform vec4 uF5; // Rough
out vec4 oFragColor;
void main(){
  TDCheckDiscard();
  vec3 N0 = normalize(vI.wN);
  vec3 P = vI.wP;
  vec3 V = normalize(camPos() - P);
  vec3 on = normalize(vI.oN);
  // per-pixel spike normal from the height field gradient (object space tangent frame)
  vec3 t1 = normalize(cross(on, abs(on.y) < 0.95 ? vec3(0,1,0) : vec3(1,0,0)));  // must match vertex shader
  vec3 t2 = cross(on, t1);
  vec2 s0 = spikeShape(vI.oP);
  float ph = uP0.x;
  float wob = 1.0 + uF3.x * sin(TAU*(ph*(1.0+floor(s0.y*3.0)) + s0.y));
  float amp = fieldAmp(vI.wP0) * (1.0 + uF3.y * (s0.y - 0.5)*2.0) * wob;
  float e = 0.03 / uF0.x;
  float hx = spikeShape(vI.oP + t1*e).x - s0.x;
  float hy = spikeShape(vI.oP + t2*e).x - s0.x;
  float A = uF0.y * amp / e;     // slope scale (object units ~ world units for unit transforms)
  // tangent frame in world space
  vec3 wt1 = normalize(vI.wT1 - N0*dot(vI.wT1, N0));
  vec3 wt2 = cross(N0, wt1);
  vec3 n = normalize(N0 - (wt1*hx + wt2*hy) * A);
  if (dot(n, V) < 0.0) n = normalize(n + V*(0.05 - dot(n,V)));
  float nv = max(dot(n,V), 0.0);
  vec3 R = reflect(-V, n);
  float ao = mix(0.15, 1.0, smoothstep(0.0, 0.5, s0.x + 0.3*(1.0-clamp(amp,0.,1.))));
  float f0 = uF4.a;
  vec3 F = schlick(vec3(f0), nv);
  vec3 col = envSample(R, uF5.x) * F * ao;
  col += uF4.rgb * (0.15 + envSample(n, 0.9) * 0.5) * ao;
  vec4 color = vec4(col, 1.0);
  TDAlphaTest(color.a);
  oFragColor = TDOutputSwizzle(color);
}
