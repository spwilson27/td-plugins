// uA: fractal(0 bulb,1 menger), power, iters, glow
// uB: camAngle(rad), distScale, fov(rad tan), ao
// uC: palette, hue, morph, wobble
// uD: tilt, elevation, steps, zoomLevels (menger: phase*Zoomloops)
// uE: spin(rad), zoomPhase01, contrast, accent
// uF: bg rgb, 0
out vec4 fragColor;
uniform vec4 uA, uB, uC, uD, uE, uF;
#define PI 3.14159265

mat3 rotY(float a){float c=cos(a),s=sin(a);return mat3(c,0,-s, 0,1,0, s,0,c);}
mat3 rotX(float a){float c=cos(a),s=sin(a);return mat3(1,0,0, 0,c,s, 0,-s,c);}

float gTrap;
float deBulb(vec3 p){
  float n = uA.y + uC.z*1.5;
  vec3 z = p; float dr = 1.0, r = 0.0; gTrap = 1e9;
  int it = int(uA.z);
  for(int i=0;i<24;i++){
    if(i>=it) break;
    r = length(z); if(r>2.0) break;
    float th = acos(clamp(z.z/r,-1.,1.)); float ph = atan(z.y,z.x);
    dr = pow(r,n-1.0)*n*dr + 1.0;
    float zr = pow(r,n); th*=n; ph*=n;
    z = zr*vec3(sin(th)*cos(ph), sin(ph)*sin(th), cos(th)) + p;
    gTrap = min(gTrap, dot(z,z));
  }
  return 0.5*log(max(r,1e-4))*r/dr;
}
float sdBox(vec3 p, vec3 b){vec3 q=abs(p)-b;return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.);}
float deMenger(vec3 p){
  // sponge in [-1,1]^3, corner (1,1,1) is a fixed point of the x3 self-similarity.
  // Level count is fractional: nEff = Iterations + zoomLevels (zoomLevels = phase*Zoomloops), the
  // last level is cross-faded in. A view at phase 1 (one more level, scale 1/3) is then identical
  // to the view at phase 0, so the loop is exact.
  float hz = exp2(-1.58496250072*uD.w);   // 3^-zoomLevels: clip box = corner sub-cube shrinking with the zoom
  float d = sdBox(p - vec3(1.0-hz), vec3(hz)); float s = 1.0; gTrap = 0.0;
  float nEff = uA.z + uD.w; float itf = floor(nEff); float wl = nEff - itf;
  float m = uC.z; // morph: rounds the cross cutters (periodic param)
  for(int i=0;i<24;i++){
    if(float(i) > itf) break;
    vec3 a = mod(p*s, 2.0) - 1.0; s *= 3.0;
    vec3 r = abs(1.0 - 3.0*abs(a));
    float da = max(r.x,r.y), db = max(r.y,r.z), dc = max(r.z,r.x);
    float c = (min(da,min(db,dc)) - 1.0 - 0.15*m*length(a))/s;
    if(float(i) == itf) c = mix(d, c, wl);   // fade the newest level in
    if(c > d){ d = c; gTrap = float(i) - uD.w; }  // trap index relative to zoom level
  }
  return d;
}
float map(vec3 p){ return uA.x < 0.5 ? deBulb(p) : deMenger(p); }
vec3 nrm(vec3 p, float e){
  vec2 k = vec2(1,-1);
  return normalize(k.xyy*map(p+k.xyy*e)+k.yyx*map(p+k.yyx*e)+k.yxy*map(p+k.yxy*e)+k.xxx*map(p+k.xxx*e));
}
vec3 pal(float t, float hue){
  int id = int(uC.x+0.5);
  if(id==0){ // bone white / warm grey
    return mix(vec3(0.35,0.33,0.3), vec3(1.0,0.97,0.9), 0.5+0.5*cos(6.2831*(t+hue)));
  } else if(id==1){ // chrome blue-grey
    return mix(vec3(0.25,0.28,0.33), vec3(0.92,0.96,1.0), 0.5+0.5*cos(6.2831*(t+hue)));
  } else if(id==2){ // bone with red accent
    float a = smoothstep(0.7,0.95, 0.5+0.5*cos(6.2831*(t*2.0+hue)));
    return mix(mix(vec3(0.3,0.3,0.3), vec3(0.95,0.93,0.88), 0.5+0.5*cos(6.2831*t)), vec3(0.9,0.05,0.04), a*uE.w);
  } else if(id==3){ // cosine rainbow-ish
    return 0.5+0.5*cos(6.2831*(vec3(1.0,1.0,1.0)*t + vec3(0.0,0.33,0.67) + hue));
  }
  return vec3(0.5+0.5*cos(6.2831*(t+hue))); // mono
}
void main(){
  vec2 res = uTDOutputInfo.res.zw;
  vec2 uv = (gl_FragCoord.xy*2.0 - res)/res.y;
  // camera
  vec3 target = vec3(0.0); float dist = 3.0*uB.y;
  vec3 ro, fw;
  mat3 R = rotY(uB.x)*rotX(-uD.y);
  if(uA.x < 0.5){
    ro = R*vec3(0,0,dist);
  } else {
    // dive into the sponge corner (1,1,1); distance shrinks by 3^-phase -> loops exactly
    target = vec3(1.0);
    vec3 dir = normalize(vec3(1.0)); 
    dir = normalize(rotY(0.3*uD.x + uC.w*sin(uE.x))*rotX(0.1 + uC.w*0.5*cos(uE.x))*dir);
    ro = target + dir*dist;
  }
  fw = normalize(target-ro);
  vec3 rt = normalize(cross(fw, vec3(0,1,0))); vec3 up = cross(rt, fw);
  float roll = (uA.x<0.5)? 0.0 : uE.x*0.0;
  vec3 rd = normalize(fw + (uv.x*rt + uv.y*up)*uB.z);
  // march
  float t = 0.0; float tmin = 0.0; float glow = 0.0; int steps = 0; bool hit = false;
  float pix = uB.z*2.0/res.y;
  int ms = int(uD.z);
  float scale = (uA.x<0.5)?1.0:dist*0.3;
  for(int i=0;i<300;i++){
    if(i>=ms) break;
    vec3 p = ro + rd*t;
    float d = map(p);
    glow += exp(-d*8.0/ (scale+0.001))*0.02;
    if(d < pix*t*0.5){ hit = true; break; }
    t += d*0.9; steps = i;
    if(t > dist*6.0) break;
  }
  vec3 col = uF.rgb;
  float gl = glow*uA.w;
  if(hit){
    vec3 p = ro + rd*t;
    vec3 n = nrm(p, max(pix*t*0.5, 1e-6));
    float trap = gTrap;
    float ct = (uA.x<0.5) ? clamp(sqrt(trap),0.,1.5)*0.7 : (trap*0.11 + 0.5*dot(n,vec3(0.3,0.5,0.2)));
    vec3 base = pal(ct, uC.y);
    vec3 L = normalize(vec3(0.6,0.8,0.5));
    float dif = max(dot(n,L),0.0);
    float rim = pow(1.0-max(dot(n,-rd),0.0), 3.0);
    float ao = 1.0 - uB.w*clamp(float(steps)/float(ms)*3.0, 0.0, 1.0);
    vec3 refl = reflect(rd, n);
    float spec = pow(max(dot(refl,L),0.0), 24.0);
    col = base*(0.12 + 0.95*dif)*ao + spec*0.5*ao + rim*0.25*base;
    col = mix(col, uF.rgb, 1.0 - exp(-t*0.0 - 0.02*t*t/(dist*dist)));
  }
  vec3 gc = pal(0.15, uC.y);
  col += gc*gl*(hit?0.8:1.0);
  col = pow(max(col,0.0), vec3(1.0/uE.z)) ;
  col = col/(1.0+0.15*col);
  col *= 1.0 - 0.25*dot(uv*0.5,uv*0.5);
  fragColor = TDOutputSwizzle(vec4(col,1.0));
}
