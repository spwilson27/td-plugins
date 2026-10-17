// One Jacobi relaxation pass of the edge-length constraints (neighbours from the Neighbor POP, rest
// lengths from RestP) plus sphere projection. Run `Iterations` times via the Passes parameter.
uniform vec4 uC;   // x = stiffness, y = max neighbours (array size), z/w unused
uniform vec4 uS;   // sphere centre xyz, radius (0 = off)
void main(){
    const uint id = TDIndex();
    if (id >= TDNumElements()) return;
    vec3 p = TDIn_P();
    if (TDIn_Pin() > 0.5) { P[id] = p; return; }
    vec3 r0 = TDIn_RestP();
    int cnt = min(int(TDIn_NumNebrs()), int(uC.y + 0.5));
    vec3 corr = vec3(0.0);
    float w = 1.0 / float(max(cnt, 1));
    for (int k = 0; k < cnt; k++) {
        uint j = TDIn_Nebr(0, id, uint(k));
        vec3 o = TDIn_P(0, j);
        float L = length(TDIn_RestP(0, j) - r0);
        vec3 d = o - p;
        float len = max(length(d), 1e-6);
        // a pinned neighbour cannot move, so we take the whole correction
        corr += d * ((len - L) / len) * w * (TDIn_Pin(0, j) > 0.5 ? 2.0 : 1.0);
    }
    p += corr * uC.x;
    if (uS.w > 0.0) {
        vec3 d = p - uS.xyz; float l = length(d);
        float r = uS.w + 0.02;
        if (l < r) p = uS.xyz + d / max(l, 1e-5) * r;
    }
    P[id] = p;
}
