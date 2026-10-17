// straight 2-point line template (x = -0.5/+0.5); Color.rgb of the template point = random seed
// uA: theta, spread, alphaBase, steps ; uB: brightness, cycles
uniform vec4 uA, uB;
float h31(vec3 p){ p = fract(p*0.3183099+0.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
vec3 rdir(vec3 s, float k){ vec3 r = vec3(h31(s+k), h31(s+k+7.3), h31(s+k+13.9))*2.0-1.0; return normalize(r+1e-4); }
mat3 rotY(float a){float c=cos(a),s=sin(a);return mat3(c,0,-s, 0,1,0, s,0,c);}
mat3 rotX(float a){float c=cos(a),s=sin(a);return mat3(1,0,0, 0,c,s, 0,-s,c);}
void main(){
  const uint id = TDIndex(); if(id >= TDNumElements()) return;
  vec3 lp = TDIn_P(); vec3 seed = TDIn_Color().rgb*13.1 + 1.0;
  float e = lp.x + 0.5;
  float th = uA.x;
  float h1 = h31(seed*1.3), h2 = h31(seed*2.1+4.0), h3 = h31(seed*0.7+9.0);
  float k1 = (h1>0.5?1.0:-1.0)*(1.0+floor(h2*2.0));      // integer revolutions -> loops
  vec3 d0 = rdir(seed, 0.0), d1 = rdir(seed, 20.0);
  // start/end on a big sphere, slowly sweeping around
  vec3 a = rotY(th*k1)*d0*uA.y; vec3 b = rotX(th*k1*0.5)*rotY(-th*k1)*d1*uA.y;
  vec3 p = mix(a, b, e);
  // appear/disappear in bursts (periodic)
  float pulse = pow(0.5+0.5*sin(th*uB.y + h3*6.2831853), 4.0);
  float step_i = floor(fract(th/6.2831853)*uA.w);
  float vis = step(0.35, h31(seed + step_i));
  P[id] = p;
  Color[id] = vec4(vec3(uB.x*pulse*vis), 1.0);
}
