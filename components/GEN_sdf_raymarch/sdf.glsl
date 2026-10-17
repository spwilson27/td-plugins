// Raymarched SDF scene. Uniforms packed in vec4s.
uniform vec4 uA; // time, K, repeat, repsize
uniform vec4 uB; // shape1, shape2, combine, scale
uniform vec4 uC; // camAngle, dist, height, fov(deg)
uniform vec4 uD; // lightAz, lightEl, shadowSoft, aoStrength
uniform vec4 uE; // fogDensity, palette, hueShift, thickness
uniform vec4 uF; // fogColor.rgb, steps
uniform vec4 uG; // isPhase, look(0 orig/1 mono), accent, 0
out vec4 fragColor;

float sdSphere(vec3 p, float r){ return length(p) - r; }
float sdBox(vec3 p, vec3 b){ vec3 q = abs(p) - b; return length(max(q,0.)) + min(max(q.x,max(q.y,q.z)),0.); }
float sdTorus(vec3 p, vec2 t){ vec2 q = vec2(length(p.xz)-t.x, p.y); return length(q)-t.y; }
float sdCapsule(vec3 p, float h, float r){ p.y -= clamp(p.y,-h,h); return length(p)-r; }
float sdGyroid(vec3 p, float th){
    vec3 q = p*3.5;
    float g = abs(dot(sin(q), cos(q.zxy)))/3.5 - th;
    return max(g*0.7, length(p) - 1.1);
}
float shape(int id, vec3 p){
    if(id==0) return sdSphere(p, 0.7);
    if(id==1) return sdBox(p, vec3(0.5)) - 0.04;
    if(id==2) return sdTorus(p, vec2(0.6,0.22));
    if(id==3) return sdCapsule(p, 0.55, 0.28);
    return sdGyroid(p, uE.w);
}
float smax(float a, float b, float k){ float h = clamp(0.5-0.5*(b-a)/k,0.,1.); return mix(b,a,h)+k*h*(1.-h); }
float smin(float a, float b, float k){ float h = clamp(0.5+0.5*(b-a)/k,0.,1.); return mix(b,a,h)-k*h*(1.-h); }

float scene(vec3 p, out float mat){
    float t = uA.x;
    float s = max(uB.w, 0.05);
    p /= s;
    if(uA.z > 0.5){ float r = uA.w; p = mod(p + 0.5*r, r) - 0.5*r; }
    float k1 = uG.x > 0.5 ? 1.0 : 0.7, k2 = uG.x > 0.5 ? 1.0 : 0.6; // integer ratios in phase mode -> seamless loop
    vec3 pa = p - vec3(sin(t)*0.45, 0., cos(t*k1)*0.2);
    vec3 pb = p + vec3(sin(t)*0.45, 0., cos(t*k1)*0.2);
    // rotate a little
    float c = cos(t*k2), sn = sin(t*k2);
    pa.xz = mat2(c,-sn,sn,c)*pa.xz; pb.yz = mat2(c,-sn,sn,c)*pb.yz;
    float da = shape(int(uB.x+0.5), pa);
    float db = shape(int(uB.y+0.5), pb);
    float k = max(uA.y, 0.0001);
    int mode = int(uB.z+0.5);
    float d;
    if(mode==0) d = smin(da, db, k);
    else if(mode==1) d = smax(da, -db, k);
    else d = smax(da, db, k);
    mat = clamp(0.5 + 0.5*(db-da)/(abs(da)+abs(db)+0.001), 0., 1.);
    d *= s;
    if(uA.z < 0.5){
        float fl = p.y*s + 1.2*s + 0.15;
        if(fl < d){ d = fl; mat = -1.; }
    }
    return d;
}
float sceneD(vec3 p){ float m; return scene(p, m); }
vec3 calcNormal(vec3 p){
    vec2 e = vec2(0.0015, 0.);
    return normalize(vec3(sceneD(p+e.xyy)-sceneD(p-e.xyy), sceneD(p+e.yxy)-sceneD(p-e.yxy), sceneD(p+e.yyx)-sceneD(p-e.yyx)));
}
float softShadow(vec3 ro, vec3 rd, float k){
    float res = 1., t = 0.03;
    for(int i=0;i<48;i++){
        float h = sceneD(ro + rd*t);
        res = min(res, k*h/t);
        t += clamp(h, 0.02, 0.4);
        if(res < 0.003 || t > 12.) break;
    }
    res = clamp(res,0.,1.);
    return res*res*(3.-2.*res);
}
float calcAO(vec3 p, vec3 n){
    float occ = 0., sca = 1.;
    for(int i=0;i<5;i++){
        float h = 0.02 + 0.12*float(i);
        occ += (h - sceneD(p + n*h))*sca; sca *= 0.85;
    }
    return clamp(1. - 1.6*occ, 0., 1.);
}
vec3 palette(float t){
    if(uG.y > 0.5) return vec3(0.62 + 0.30*cos(6.2831*t)); // mono: bone-white / grey
    int id = int(uE.y+0.5);
    t += uE.z;
    vec3 a, b, c, d;
    if(id==0){ a=vec3(.5,.5,.5); b=vec3(.5); c=vec3(1.); d=vec3(0.,.33,.67); }      // rainbow
    else if(id==1){ a=vec3(.5,.4,.4); b=vec3(.5,.4,.3); c=vec3(1.,1.,.8); d=vec3(0.,.1,.2); } // sunset
    else if(id==2){ a=vec3(.2,.5,.6); b=vec3(.3,.4,.4); c=vec3(1.,1.,1.); d=vec3(.0,.25,.5); } // ocean
    else if(id==3){ a=vec3(.5); b=vec3(.5); c=vec3(2.,1.,0.); d=vec3(.5,.2,.25); }  // neon
    else { return vec3(0.75 + 0.25*cos(6.2831*t)); }                                // mono
    return a + b*cos(6.28318*(c*t+d));
}
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = (vUV.st*2. - 1.) * vec2(res.x/res.y, 1.);
    float ang = uC.x;
    vec3 ro = vec3(sin(ang)*uC.y, uC.z, cos(ang)*uC.y);
    vec3 ta = vec3(0.);
    vec3 ww = normalize(ta-ro), uu = normalize(cross(ww, vec3(0,1,0))), vv = cross(uu, ww);
    float fl = 1.0/tan(radians(uC.w)*0.5);
    vec3 rd = normalize(uv.x*uu + uv.y*vv + fl*ww);

    float t = 0.; float mat = 0.; bool hit = false;
    int maxSteps = int(uF.w);
    for(int i=0;i<256;i++){
        if(i>=maxSteps) break;
        float m; vec3 p = ro + rd*t;
        float d = scene(p, m);
        if(d < 0.0008*t){ hit = true; mat = m; break; }
        t += d*0.9;
        if(t > 40.) break;
    }
    vec3 bg = uG.y > 0.5 ? vec3(0.) : uF.rgb;
    vec3 col = bg*(0.6 + 0.4*(vUV.t));
    if(hit){
        vec3 p = ro + rd*t;
        vec3 n = calcNormal(p);
        vec3 base;
        if(mat < -0.5){
            vec2 g = floor(p.xz*1.0);
            base = vec3(0.12 + 0.1*mod(g.x+g.y,2.0));
            base = mix(base, palette(0.1)*0.3, 0.3);
            if(uG.y > 0.5) base = vec3(0.015 + 0.03*mod(g.x+g.y,2.0));
        } else {
            base = palette(mat*0.5 + length(p)*0.12 + dot(n, vec3(.3,.2,.1))*0.25);
            if(uG.y > 0.5) base = mix(base, vec3(0.85,0.03,0.03), uG.z*smoothstep(0.5,0.75,mat));
        }
        vec3 L = normalize(vec3(cos(uD.y)*sin(uD.x), sin(uD.y), cos(uD.y)*cos(uD.x)));
        float dif = clamp(dot(n,L),0.,1.);
        float sh = softShadow(p + n*0.01, L, uD.z);
        float ao = mix(1., calcAO(p,n), uD.w);
        float sky = 0.5 + 0.5*n.y;
        float spe = pow(clamp(dot(reflect(rd, n), L), 0., 1.), 24.);
        vec3 lin = vec3(1.2,1.05,0.9)*dif*sh + vec3(0.25,0.3,0.4)*sky*ao + 0.15*ao;
        col = base*lin + spe*sh*0.5*ao;
        float fog = 1. - exp(-uE.x*uE.x*t*t*0.02);
        col = mix(col, bg, fog);
    }
    col = pow(col, vec3(0.4545));
    fragColor = TDOutputSwizzle(vec4(col, 1.));
}
