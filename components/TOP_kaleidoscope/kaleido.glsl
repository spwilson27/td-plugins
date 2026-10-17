uniform vec4 uA; // mode, segments, rotation(rad), zoom
uniform vec4 uB; // centerX, centerY, animPhase, tiles
uniform vec4 uC; // hyperQ, srcZoom, animate, 0
uniform vec4 uD; // unused, look(1=mono), accent, 0
out vec4 fragColor;
const float PI = 3.14159265359;
vec2 rot(vec2 p, float a){ float c=cos(a), s=sin(a); return vec2(c*p.x - s*p.y, s*p.x + c*p.y); }

vec2 foldRadial(vec2 v, float n){
    float seg = 2.*PI/n;
    float r = length(v);
    float a = atan(v.y, v.x);
    a = mod(a, seg);
    a = abs(a - seg*0.5);
    return r*vec2(cos(a), sin(a));
}
vec2 cmul(vec2 a, vec2 b){ return vec2(a.x*b.x - a.y*b.y, a.x*b.y + a.y*b.x); }
vec2 cdiv(vec2 a, vec2 b){ return cmul(a, vec2(b.x, -b.y)) / dot(b,b); }

void main(){
    vec2 res = uTDOutputInfo.res.zw;
    float aspect = res.x/res.y;
    vec2 p = (vUV.st - 0.5) * vec2(aspect, 1.0) * 2.0;     // roughly [-1,1] on the short axis
    p /= max(uA.w, 1e-3);
    int mode = int(uA.x + 0.5);
    float ph = uB.z;
    float kA = 0.5, kB = 0.4, kC = 0.37, kD = 0.53;
    vec2 q; bool outside = false; float shade = 1.0;
    float sz = max(uC.y, 1e-3);

    if(mode == 0){                       // N-fold radial
        vec2 v = rot(p - vec2(uB.x, uB.y)*2.0, -uA.z);
        v = foldRadial(v, max(floor(uA.y + 0.5), 1.0));
        q = 0.5 + rot(v, uC.z*(ph*0.15)) * 0.5 / sz;
    } else if(mode == 1){                // square mirror tiles
        vec2 v = rot(p - vec2(uB.x, uB.y)*2.0, -uA.z) * uB.w * 0.5 + 0.15*uC.z*vec2(sin(ph*kA), cos(ph*kB));
        q = abs(mod(v, 2.0) - 1.0);      // mirrored repeat 0..1
        q = 0.5 + (q - 0.5) / sz;
    } else if(mode == 2){                // triangle (kaleidoscopic *333) tiling
        vec2 v = rot(p - vec2(uB.x, uB.y)*2.0, -uA.z) * uB.w * 0.4 + 0.2*uC.z*vec2(sin(ph*kA), cos(ph*kB));
        // lattice reduction
        vec2 a = vec2(0., 1.7320508), b = vec2(1.5, -0.8660254);
        float det = a.x*b.y - a.y*b.x;
        vec2 st = vec2((v.x*b.y - v.y*b.x), (-v.x*a.y + v.y*a.x)) / det;
        st = fract(st);
        v = st.x*a + st.y*b;
        vec2 n1 = vec2(0., 1.), n2 = vec2(0.8660254, -0.5), n3 = vec2(-0.8660254, -0.5);
        for(int i=0;i<10;i++){
            v -= 2.*min(0., dot(v, n1))*n1;
            v -= 2.*min(0., dot(v, n2))*n2;
            v -= 2.*min(0., dot(v - vec2(1.,0.), n3))*n3;
        }
        q = 0.5 + (v - vec2(0.5, 0.2887)) * 0.9 / sz;
    } else if(mode == 3){                // hexagonal tiling, 6-fold mirror in each cell
        vec2 v = rot(p - vec2(uB.x, uB.y)*2.0, -uA.z) * uB.w * 0.5 + 0.2*uC.z*vec2(sin(ph*kA), cos(ph*kB));
        // nearest hex-lattice centre
        vec2 s = vec2(1., 1.7320508);
        vec2 h = s*0.5;
        vec2 a1 = mod(v, s) - h;
        vec2 b1 = mod(v - h, s) - h;
        vec2 g = dot(a1,a1) < dot(b1,b1) ? a1 : b1;
        g = foldRadial(g, 6.0);
        q = 0.5 + g * 0.7 / sz;
    } else {                             // Poincare disk {p,q} hyperbolic tiling
        float P = max(floor(uA.y + 0.5), 3.0);
        float Q = max(floor(uC.x + 0.5), 3.0);
        // keep the tiling hyperbolic: (P-2)(Q-2) > 4
        if((P-2.)*(Q-2.) <= 4.0001) Q = floor(4.0/(P-2.)) + 3.0;
        vec2 z = rot(p, -uA.z) * 0.98;
        if(dot(z,z) >= 1.0){ outside = true; }
        // moebius drift / centre offset
        vec2 c0 = vec2(uB.x, uB.y)*1.6 + uC.z*0.35*vec2(sin(ph*kC), cos(ph*kD));
        float cl = length(c0); if(cl > 0.9) c0 *= 0.9/cl;
        z = cdiv(z - c0, vec2(1.,0.) - cmul(vec2(c0.x,-c0.y), z));
        float a = PI/P, bq = PI/Q;
        float cb = cos(bq), sa = sin(a);
        float cx = cb / sqrt(max(cb*cb - sa*sa, 1e-4));
        float r = sqrt(max(cx*cx - 1., 1e-4));
        vec2 cc = vec2(cx, 0.);
        vec2 n2 = vec2(sa, -cos(a));
        float count = 0.;
        for(int i=0;i<40;i++){
            z.y = abs(z.y);
            z -= 2.*min(0., dot(z, n2))*n2;
            vec2 d = z - cc; float dd = dot(d,d);
            if(dd < r*r){ z = cc + d*(r*r/dd); count += 1.; }
            else if(i > 3 && dot(z,n2) >= 0.) break;
        }
        float e = cx - r;
        q = 0.5 + (z - vec2(e*0.45, e*0.12)) / (e*1.1*sz);
        shade = 0.75 + 0.25*mod(count, 2.0);
        shade *= smoothstep(1.0, 0.97, length(rot(p,-uA.z)*0.98));
    }
    vec3 col = texture(sTD2DInputs[0], q).rgb * shade;
    if(uD.y > 0.5){
        float l = dot(col, vec3(0.299,0.587,0.114));
        l = 0.9*pow(smoothstep(0.08, 1.05, l), 1.9);
        col = vec3(l) * vec3(0.96,0.94,0.89);
        col = mix(col, vec3(0.95,0.03,0.03) * (0.25 + 0.9*l), uD.z * smoothstep(0.35, 0.6, l) * (1.0 - smoothstep(0.7, 0.95, l)));
    }
    if(outside) col = vec3(0.0);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
