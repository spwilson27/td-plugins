// uA: bands, banding, bandshift, steps(k per loop)
// uB: theta, scale, shape(0 blob,1 sphere,2 torus,3 image,4 pop input), depth
// uC: threshold, samples, pointsize, jitter
// uD: camUnit xyz, brightness ; uE: sweepamt, sweepcycles, 0, 0
uniform vec4 uA, uB, uC, uD, uE;
float h31(vec3 p){ p = fract(p*0.3183099+0.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vn(vec3 x){
  vec3 i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(h31(i),h31(i+vec3(1,0,0)),f.x), mix(h31(i+vec3(0,1,0)),h31(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(h31(i+vec3(0,0,1)),h31(i+vec3(1,0,1)),f.x), mix(h31(i+vec3(0,1,1)),h31(i+vec3(1,1,1)),f.x),f.y),f.z);
}
float hid(uint i, float k){ return fract(sin(float(i)*12.9898+k*78.233)*43758.5453); }
void main(){
  const uint id = TDIndex(); if(id >= TDNumElements()) return;
  vec3 p = TDIn_P();
  int shape = int(uB.z+0.5);
  float keep = 1.0; float lum = 0.7;
  vec3 n = normalize(p+1e-5);
  float th = uB.x;
  if(shape==3){
    vec2 uv = p.xy*0.5+0.5;
    vec3 t = texture(uTex, uv).rgb; lum = dot(t, vec3(0.299,0.587,0.114));
    float prob = smoothstep(uC.x, 1.0, lum)*uC.y;
    keep = (hid(id,9.0) < prob) ? 1.0 : 0.0;
    p = vec3(p.xy*1.25, (lum-0.5)*uB.w);
    n = vec3(0,0,1);
  } else if(shape==2){
    vec3 rc = normalize(vec3(p.x,0.0,p.z))*0.9; n = normalize(p-rc);
  } else if(shape==0){
    p.y *= 1.28; p.x *= 0.82;
    vec3 q = p - vec3(0,0.05,0.9);
    p += n*(vn(p*2.2)*0.26 - 0.13) + vec3(0,0,1)*exp(-dot(q,q)*14.0)*0.34;
    p.y -= 0.12*smoothstep(-0.2,-1.0,p.y)*(1.0-abs(p.x));  // jaw hint
    n = normalize(p+1e-5);
  } else if(shape==4){
    p *= uB.y;
  }
  if(shape<3) p *= uB.y;
  // strata banding: snap into horizontal slices (laser-scan look) + per-band scan offset
  float B = max(uA.x, 1.0);
  float yb = (floor(p.y*B)+0.5)/B;
  float band = floor(p.y*B);
  float step_i = mod(floor(fract(th/6.2831853)*uA.w), max(uA.w,1.0));
  float shift = (h31(vec3(band, step_i, 1.7))-0.5) * uA.z * 2.0 * step(0.7, h31(vec3(band, step_i, 5.1)));
  p.y = mix(p.y, yb, uA.y);
  p.x += shift*uA.y;
  // keep only a share of rows when strongly banded (gaps between scanlines)
  // jitter
  vec3 rnd = vec3(hid(id,1.0),hid(id,2.0),hid(id,3.0)) - 0.5;
  p += rnd*uC.w*(0.5+0.5*sin(th + hid(id,4.0)*6.2831853));
  // sweeping scan plane
  float sw = fract(th/6.2831853*uE.y);
  float sy = mix(-1.5, 1.5, sw);
  float sweep = exp(-pow((p.y - sy)*5.0, 2.0)) * uE.x;
  float facing = 0.5+0.5*dot(n, normalize(uD.xyz));
  float depthc = mix(0.35, 1.0, smoothstep(-1.2, 1.2, dot(p, normalize(uD.xyz))));
  float shade = (0.35 + 0.65*facing) * depthc * (0.6+0.4*hid(id,6.0));
  float b = shade*uD.w*(1.0+sweep*3.0);
  P[id] = p;
  Color[id] = vec4(vec3(b), 1.0);
  PointScale[id] = uC.z*(0.7+0.6*hid(id,7.0))*(1.0+sweep*1.2);
  Keep[id] = keep;
}
