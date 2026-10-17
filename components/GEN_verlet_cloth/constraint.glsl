// One Jacobi relaxation pass of structural + shear distance constraints (+ sphere collider).
// in0 = positions (previous pass), in1 = rest/pin. Run `Iterations` times via npasses.
uniform vec4 uC;   // x=N y=cloth size z=stiffness w=unused
uniform vec4 uS;   // sphere centre xyz, radius (0 = off)
out vec4 fragColor;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    int N = int(uC.x + 0.5);
    vec4 me = texelFetch(sTD2DInputs[0], ip, 0);
    vec4 rest = texelFetch(sTD2DInputs[1], ip, 0);
    if (rest.a > 0.5) { fragColor = vec4(rest.xyz, 1.0); return; }
    float h = uC.y / float(N - 1);
    vec3 p = me.xyz;
    vec3 corr = vec3(0.0);
    for (int j = -1; j <= 1; j++)
        for (int i = -1; i <= 1; i++) {
            if (i == 0 && j == 0) continue;
            ivec2 q = ip + ivec2(i, j);
            if (q.x < 0 || q.y < 0 || q.x >= N || q.y >= N) continue;
            float L = (i != 0 && j != 0) ? h * 1.41421356 : h;
            float w = (i != 0 && j != 0) ? 0.12 : 0.25;
            vec4 o = texelFetch(sTD2DInputs[0], q, 0);
            float pinned = texelFetch(sTD2DInputs[1], q, 0).a;
            vec3 d = o.xyz - p;
            float len = max(length(d), 1e-6);
            // a pinned neighbour can't move, so we take the whole correction
            corr += d * ((len - L) / len) * w * (pinned > 0.5 ? 2.0 : 1.0);
        }
    p += corr * uC.z;
    if (uS.w > 0.0) {
        vec3 d = p - uS.xyz; float l = length(d);
        float r = uS.w + 0.02;
        if (l < r) p = uS.xyz + d / max(l, 1e-5) * r;
    }
    fragColor = vec4(p, 1.0);
}
