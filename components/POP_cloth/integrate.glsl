// Verlet step. in0 = cloth state (feedback), in1 = live input mesh (pinned points follow it).
uniform vec4 uG;   // xyz gravity, w damping
uniform vec4 uW;   // x wind strength, y turbulence, z time (s), w noise frequency
uniform vec4 uD;   // xyz wind direction, w play
uniform vec4 uS;   // sphere centre xyz, radius (0 = off)
uniform vec4 uF;   // x = dt^2 scale
void main(){
    const uint id = TDIndex();
    if (id >= TDNumElements()) return;
    vec3 cur = TDIn_P(0, id);
    vec3 prv = TDIn_PrevP(0, id);
    if (TDIn_Pin(1, id) > 0.5) {                   // pinned: follow the live input mesh
        vec3 q = TDIn_P(1, id);
        P[id] = q; PrevP[id] = q; return;
    }
    if (uD.w < 0.5) { P[id] = cur; PrevP[id] = prv; return; }
    float t = uW.z;
    vec3 p = cur * uW.w;
    float n1 = TDSimplexNoise(vec4(p.xy, p.z, t * 0.7));
    float n2 = TDSimplexNoise(vec4(p.yz + 11.3, p.x, t * 0.7 + 3.1));
    float n3 = TDSimplexNoise(vec4(p.zx + 5.1, p.y, t * 0.7 + 7.7));
    vec3 wind = uD.xyz * uW.x * (1.0 + uW.y * n3) + uW.x * uW.y * 0.5 * vec3(n1, n2, 0.5 * n3);
    vec3 acc = uG.xyz + wind;
    vec3 v = (cur - prv) * (1.0 - uG.w);
    vec3 np = cur + v + acc * uF.x;
    if (uS.w > 0.0) {
        vec3 d = np - uS.xyz; float l = length(d);
        float r = uS.w + 0.02;
        if (l < r) np = uS.xyz + d / max(l, 1e-5) * r;
    }
    P[id] = np;
    PrevP[id] = cur;
}
