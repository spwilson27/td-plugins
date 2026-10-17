// ---- procedural studio environment (shared) ----
// uP0: x=ph(0..1) y=Envmix z=Envrot w=Envgain ; uP1.x = Accent
uniform vec4 uP0;
uniform vec4 uP1;
uniform sampler2D sEnv;
#define PI 3.14159265359
#define TAU 6.28318530718
float rbox(float x, float c, float hw, float soft){ return 1.0 - smoothstep(hw-soft, hw+soft, abs(x-c)); }
float awrap(float a){ return mod(a+PI, TAU) - PI; }
vec3 studioEnv(vec3 d, float soft){
  float az = awrap(atan(d.x, d.z) - uP0.z*TAU);
  float el = asin(clamp(d.y,-1.,1.));
  soft = 0.03 + soft;
  vec3 c = mix(vec3(0.004,0.004,0.005), vec3(0.03,0.032,0.038), smoothstep(-0.6,0.9,el));
  // overhead large softbox
  float top = rbox(el, 1.15, 0.30, soft*1.5) * rbox(az, 0.0, 2.2, 0.5+soft);
  c += vec3(1.0,0.98,0.95) * 5.0 * top;
  // two vertical strip lights, left/right front
  float s1 = rbox(az, 0.95, 0.16, soft) * rbox(el, 0.25, 0.65, soft*1.5);
  float s2 = rbox(az,-1.05, 0.10, soft) * rbox(el, 0.20, 0.60, soft*1.5);
  c += vec3(0.85,0.92,1.0) * 3.5 * s1 + vec3(1.0,0.95,0.9) * 2.5 * s2;
  // thin rim strip behind
  float s3 = rbox(abs(az), 2.75, 0.07, soft) * rbox(el, 0.1, 0.5, soft*1.5);
  c += vec3(1.0) * 3.0 * s3;
  // low red accent bar (front, below horizon)
  float s4 = rbox(az, 0.2, 0.6, soft) * rbox(el, -0.42, 0.045, soft);
  c += vec3(1.0,0.06,0.04) * 4.0 * uP1.x * s4;
  // faint floor bounce
  c += vec3(0.03,0.03,0.035) * smoothstep(-0.1,-1.0,el) * 0.5;
  return c;
}
vec3 envSample(vec3 d, float soft){
  vec3 c = studioEnv(d, soft);
  if (uP0.y > 0.001){
    vec2 uv = vec2(atan(d.x,-d.z)/TAU + 0.5 + uP0.z, acos(clamp(d.y,-1.,1.))/PI);
    vec3 e = textureLod(sEnv, vec2(fract(uv.x), uv.y), soft*8.0).rgb;
    c = mix(c, e, uP0.y);
  }
  return c * uP0.w;
}
vec3 camPos(){ return uTDMats[0].camInverse[3].xyz; }
// ---- hash / noise ----
float h11(float p){ p=fract(p*.1031); p*=p+33.33; p*=p+p; return fract(p); }
float h13(vec3 p3){ p3=fract(p3*.1031); p3+=dot(p3,p3.zyx+31.32); return fract((p3.x+p3.y)*p3.z); }
vec3 h33(vec3 p3){ p3=fract(p3*vec3(.1031,.1030,.0973)); p3+=dot(p3,p3.yxz+33.33); return fract((p3.xxy+p3.yxx)*p3.zyx); }
float vnoise(vec3 p){
  vec3 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(h13(i),h13(i+vec3(1,0,0)),f.x), mix(h13(i+vec3(0,1,0)),h13(i+vec3(1,1,0)),f.x), f.y),
             mix(mix(h13(i+vec3(0,0,1)),h13(i+vec3(1,0,1)),f.x), mix(h13(i+vec3(0,1,1)),h13(i+vec3(1,1,1)),f.x), f.y), f.z);
}
float fbm3(vec3 p){ float a=0.5, s=0.0; for(int i=0;i<4;i++){ s+=a*vnoise(p); p=p*2.03+vec3(7.1,3.7,1.3); a*=0.5;} return s; }
vec3 schlick(vec3 f0, float c){ return f0 + (1.0-f0)*pow(1.0-clamp(c,0.,1.),5.0); }
