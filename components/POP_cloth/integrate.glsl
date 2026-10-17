// Verlet integration. in0 = current positions, in1 = previous positions, in2 = rest/pin. a=1 once initialised.
uniform vec4 uG;   // xyz gravity, w damping
uniform vec4 uW;   // x wind strength, y turbulence, z loop phase 0-1, w reset
uniform vec4 uD;   // xyz wind direction, w play
uniform vec4 uS;   // sphere centre xyz, radius (0 = off)
uniform vec4 uF;   // x = dt^2 scale
out vec4 fragColor;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec4 cur = texelFetch(sTD2DInputs[0], ip, 0);
    vec4 prv = texelFetch(sTD2DInputs[1], ip, 0);
    vec4 rest = texelFetch(sTD2DInputs[2], ip, 0);
    if (uW.w > 0.5 || cur.a < 0.5) { fragColor = vec4(rest.xyz, 1.0); return; }
    if (uD.w < 0.5) { fragColor = cur; return; }
    if (prv.a < 0.5) prv = cur;
    if (rest.a > 0.5) { fragColor = vec4(rest.xyz, 1.0); return; }
    vec3 p = cur.xyz;
    float a = 6.2831853 * uW.z;                       // loop phase 0..1 -> circle in 4D noise: periodic wind
    vec2 cs = 0.8 * vec2(cos(a), sin(a));
    float n1 = TDSimplexNoise(vec4(p.xy * 1.7, cs));
    float n2 = TDSimplexNoise(vec4(p.xy * 1.7 + 11.3, cs.yx * vec2(1.0,-1.0)));
    float n3 = TDSimplexNoise(vec4(p.xy * 1.3 + 5.1, -cs));
    vec3 wind = uD.xyz * uW.x * (1.0 + uW.y * n3) + uW.x * uW.y * 0.5 * vec3(n1, n2, 0.5 * n3);
    vec3 acc = uG.xyz + wind;
    vec3 v = (cur.xyz - prv.xyz) * (1.0 - uG.w);
    vec3 np = cur.xyz + v + acc * uF.x;
    if (uS.w > 0.0) {
        vec3 d = np - uS.xyz; float l = length(d);
        float r = uS.w + 0.02;
        if (l < r) np = uS.xyz + d / max(l, 1e-5) * r;
    }
    fragColor = vec4(np, 1.0);
}
