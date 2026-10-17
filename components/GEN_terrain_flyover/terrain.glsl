// uA: amp, freq, zperiod(cells), scroll(world units)
// uB: valley, valleywidth, sourceImage(0/1), style(0 rolling,1 ridged,2 terraced)
// uC: mode(0 wire,1 solid), fogstart, fogend, bright
// uD: wire rgb, redaccent
// uE: solid rgb, texlen (world length of image tile)
// uF: gridW, gridL, 0,0
uniform vec4 uA, uB, uC, uD, uE, uF;
float h21(vec2 p){ p = fract(p*vec2(0.1031,0.1030)); p += dot(p, p.yx+33.33); return fract((p.x+p.y)*p.x); }
// value noise periodic in z (lattice wraps every `per` cells)
float vn(vec2 x, float per){
  vec2 i = floor(x), f = fract(x); f = f*f*(3.0-2.0*f);
  float z0 = mod(i.y, per), z1 = mod(i.y+1.0, per);
  float a = h21(vec2(i.x, z0)), b = h21(vec2(i.x+1.0, z0)), c = h21(vec2(i.x, z1)), d = h21(vec2(i.x+1.0, z1));
  return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}
float heightf(float x, float z){
  float zz = z + uA.w;               // scrolled coordinate
  float h;
  if(uB.z > 0.5){
    float L = max(uE.w, 1e-3);
    float v = zz / L; v = abs(fract(v*0.5)*2.0 - 1.0);  // mirrored -> continuous everywhere, period 2L
    vec2 uv = vec2(x/uF.x + 0.5, v);
    vec3 t = texture(uTex, uv).rgb; h = dot(t, vec3(0.299,0.587,0.114));
  } else {
    vec2 p = vec2(x, zz)*uA.y; float per = uA.z; float a = 0.5, s = 0.0, tot = 0.0;
    for(int o=0;o<5;o++){
      float n = vn(p + float(o)*17.3*vec2(1,0), per);
      if(uB.w > 0.5 && uB.w < 1.5) n = 1.0 - abs(2.0*n-1.0);
      s += n*a; tot += a; a *= 0.5; p *= 2.0; per *= 2.0;
    }
    h = s/tot;
    if(uB.w > 1.5){ h = floor(h*7.0)/7.0 + 0.5*smoothstep(0.0,1.0,fract(h*7.0))/7.0; }
  }
  float ax = abs(x)/(uF.x*0.5);
  float v = mix(1.0, smoothstep(uB.y*0.5, uB.y*0.5+0.35, ax), uB.x);   // flat road/valley in the middle
  return h*uA.x*v;
}
void main(){
  const uint id = TDIndex(); if(id >= TDNumElements()) return;
  vec3 g = TDIn_P();
  float x = g.x, z = g.y + uF.y*0.5;          // z in 0..L (distance ahead)
  float h = heightf(x, z);
  P[id] = vec3(x, h, -z);
  float dist = z/uF.y;
  float fog = pow(mix(0.03, 1.0, 1.0 - smoothstep(uC.y, uC.z, dist)), 1.3);
  fog *= smoothstep(0.0, 0.04, dist);
  vec3 col;
  if(uC.x < 0.5){
    float cidx = floor((x/uF.x+0.5)*1000.0);
    float acc = step(1.0 - 0.06*uD.w, h21(vec2(cidx, 3.0)));
    vec3 base = mix(uD.rgb, vec3(1.0,0.06,0.04), acc*0.95);
    col = base * (0.55 + 0.9*h/max(uA.x,1e-3)) * uC.w;
  } else {
    float e = 0.15;
    vec3 n = normalize(vec3(heightf(x-e,z)-heightf(x+e,z), 2.0*e, heightf(x,z-e)-heightf(x,z+e)));
    float l = max(dot(n, normalize(vec3(0.3,0.8,-0.5))), 0.0);
    col = uE.rgb*(0.4 + 1.6*l) + 0.03*h/max(uA.x,1e-3);
  }
  Color[id] = vec4(col*fog, 1.0);
}
