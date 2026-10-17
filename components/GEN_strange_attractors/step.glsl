// Particle integrator. State (rgba32float): xyz = position in normalised attractor space, w = 1 + speed (0 = uninitialised)
uniform vec4 uA;   // x=type A, y=type B, z=morph, w=reset
uniform vec4 uB;   // x=speed (h), y=loop angle, z=substeps, w=seed
uniform vec4 uC;   // x=coef modulation amount, y=coef modulation speed
out vec4 fragColor;

const vec3  CEN[5] = vec3[5](vec3(0.0, 0.0, 22.4), vec3(0.0, 0.0, 0.6), vec3(0.0), vec3(-3.0, -3.0, -3.0), vec3(1.0, 0.0, 0.4));
const float SCL[5] = float[5](24.0, 1.6, 4.0, 6.5, 11.0);
const float DTS[5] = float[5](0.006, 0.012, 0.09, 0.006, 0.006);

float hash(vec3 p){ p = fract(p*vec3(443.897,441.423,437.195)); p += dot(p,p.yzx+19.19); return fract((p.x+p.y)*p.z); }

vec3 F(int t, vec3 p, float m){
    if (t == 0) {            // Lorenz
        float s = 10.0, r = 28.0*(1.0+0.25*m), b = 8.0/3.0;
        return vec3(s*(p.y-p.x), p.x*(r-p.z)-p.y, p.x*p.y-b*p.z);
    } else if (t == 1) {     // Aizawa
        float a = 0.95+0.15*m, b = 0.7, c = 0.6, d = 3.5, e = 0.25, f = 0.1;
        return vec3((p.z-b)*p.x - d*p.y, d*p.x + (p.z-b)*p.y,
                    c + a*p.z - p.z*p.z*p.z/3.0 - (p.x*p.x+p.y*p.y)*(1.0+e*p.z) + f*p.z*p.x*p.x*p.x);
    } else if (t == 2) {     // Thomas
        float b = 0.208186*(1.0+0.35*m);
        return vec3(sin(p.y)-b*p.x, sin(p.z)-b*p.y, sin(p.x)-b*p.z);
    } else if (t == 3) {     // Halvorsen
        float a = 1.4*(1.0+0.15*m);
        return vec3(-a*p.x-4.0*p.y-4.0*p.z-p.y*p.y, -a*p.y-4.0*p.z-4.0*p.x-p.z*p.z, -a*p.z-4.0*p.x-4.0*p.y-p.x*p.x);
    } else {                 // Dadras
        float a = 3.0, b = 2.7, c = 1.7+0.3*m, d = 2.0, e = 9.0;
        return vec3(p.y-a*p.x+b*p.y*p.z, c*p.y-p.x*p.z+p.z, d*p.x*p.y-e*p.z);
    }
}
vec3 fn(int t, vec3 q, float m){ return DTS[t]*F(t, CEN[t]+SCL[t]*q, m)/SCL[t]; }

void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec4 s = texelFetch(sTD2DInputs[0], ip, 0);
    vec3 q = s.xyz;
    int ta = int(uA.x+0.5), tb = int(uA.y+0.5);
    if (uA.w > 0.5 || s.w < 0.5) {
        vec3 r = vec3(hash(vec3(ip, 1.0+uB.w)), hash(vec3(ip, 2.0+uB.w)), hash(vec3(ip, 3.0+uB.w)));
        fragColor = vec4((r-0.5)*0.8, 1.0); return;
    }
    float m = uC.x*sin(uB.y);   // uB.y = loop angle (2*pi*phase*cycles): coefficient wobble is loop-periodic
    float mor = clamp(uA.z, 0.0, 1.0);
    float h = uB.x;
    float spd = 0.0;
    int n = clamp(int(uB.z+0.5), 1, 24);
    // Morph = fraction of the particle population that follows attractor B (stable per-particle threshold).
    // Each particle always integrates a *real* attractor, so both shapes stay sharp while the population cross-fades.
    int t = (hash(vec3(vec2(ip), 9.0)) < mor) ? tb : ta;
    for (int i = 0; i < n; i++) {
        vec3 k1 = fn(t, q, m);
        vec3 k2 = fn(t, q + 0.5*h*k1, m);
        q += h*k2;
        spd = length(k2);
    }
    if (!(abs(q.x) < 8.0 && abs(q.y) < 8.0 && abs(q.z) < 8.0)) {   // diverged / NaN -> respawn
        vec3 r = vec3(hash(vec3(ip, 5.0+uB.y)), hash(vec3(ip, 6.0+uB.y)), hash(vec3(ip, 7.0+uB.y)));
        q = (r-0.5)*0.4; spd = 0.0;
    }
    fragColor = vec4(q, 1.0 + spd);
}
