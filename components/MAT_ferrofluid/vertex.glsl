out Vertex { vec3 oP; vec3 oN; vec3 wP; vec3 wN; vec3 wP0; float hgt; vec3 wT1; } vO;
void main(){
  vec3 pos = TDPos();
  vec3 n = normalize(TDNormal());
  vec4 w0 = TDDeform(pos);
  vec3 wn = normalize(TDDeformNorm(n));
  vec2 sp = spikeShape(pos);
  float ph = uP0.x;
  float wob = 1.0 + uF3.x * sin(TAU*(ph*(1.0+floor(sp.y*3.0)) + sp.y));   // loops: integer harmonics
  float amp = fieldAmp(w0.xyz) * (1.0 + uF3.y * (sp.y - 0.5)*2.0) * wob;
  float H = uF0.y * amp * sp.x;
  vec3 toA = uF2.xyz - w0.xyz;
  vec3 dir = normalize(wn + uF2.w * normalize(toA) * smoothstep(0.0, 1.0, sp.x) * min(amp, 1.0));
  vec3 wp = w0.xyz + dir * H;
  vec3 t1 = normalize(cross(n, abs(n.y) < 0.95 ? vec3(0,1,0) : vec3(1,0,0)));
  vO.wT1 = normalize(TDDeformNorm(t1));
  vO.oP = pos; vO.oN = n; vO.wP0 = w0.xyz; vO.wP = wp; vO.wN = wn; vO.hgt = sp.x;
  gl_Position = TDWorldToProj(vec4(wp, 1.0));
}
