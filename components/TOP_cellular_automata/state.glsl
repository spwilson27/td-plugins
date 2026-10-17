// Cellular automata state. r=state g=age b=ghost(fade after death) a=initialised flag
// input 0 = previous state (feedback), input 1 = source image
uniform vec4 uA;   // x=rule(0 life,1 brain,2 wireworld,3 LtL,4 custom B/S) y=reset z=density w=step
uniform vec4 uB;   // x=Bmask y=Smask z=radius w=threshold (luminance)
uniform vec4 uC;   // LtL: birth lo, birth hi, survive lo, survive hi (fractions of neighbourhood)
uniform vec4 uD;   // x=ghost decay y=seed z=invert w=frame number
uniform vec4 uE;   // x=injection probability per step (on cells where the input is bright)
out vec4 fragColor;

float hash(vec2 p){ p = fract(p*vec2(443.897,441.423) + uD.y*0.137); p += dot(p,p.yx+19.19); return fract((p.x+p.y)*p.x); }
float hash2(vec2 ip, float t){
    vec3 p = fract(vec3(ip, t) * vec3(.1031, .1030, .0973));
    p += dot(p, p.yzx + 33.33);
    return fract((p.x + p.y) * p.z);
}
bool maskAt(vec2 uv){
    vec3 sc = texture(sTD2DInputs[1], uv).rgb;
    float l = dot(sc, vec3(0.299, 0.587, 0.114));
    bool on = l > uB.w;
    return uD.z > 0.5 ? !on : on;
}

void main(){
    ivec2 res = ivec2(uTDOutputInfo.res.zw);
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec2 uv = (vec2(ip) + 0.5) / vec2(res);
    vec4 c = texelFetch(sTD2DInputs[0], ip, 0);
    int rule = int(uA.x + 0.5);

    if (uA.y > 0.5 || c.a < 0.5) {            // (re)seed from the input image
        bool m = maskAt(uv);
        float h = hash(vec2(ip) + 0.5);
        float s = 0.0;
        if (m) {
            if (rule == 2) {                   // wireworld: input = conductors, a few electron heads
                s = 3.0;
                if (hash(vec2(ip) + 31.7) < 0.03) s = 1.0;
            } else if (rule == 1) {            // brain: on / dying
                if (h < uA.z) s = hash(vec2(ip) + 9.3) < 0.3 ? 2.0 : 1.0;
            } else if (h < uA.z) s = 1.0;
        }
        fragColor = vec4(s, 0.0, s > 0.5 ? 1.0 : 0.0, 1.0);
        return;
    }
    if (uA.w < 0.5) { fragColor = c; return; }

    float s = c.r;
    float ns = s;
    if (rule == 3) {
        int R = clamp(int(uB.z + 0.5), 1, 15);
        float n = 0.0;
        for (int j = -R; j <= R; j++)
            for (int i = -R; i <= R; i++) {
                if (i == 0 && j == 0) continue;
                ivec2 q = (ip + ivec2(i, j) + res) % res;
                n += texelFetch(sTD2DInputs[0], q, 0).r > 0.5 ? 1.0 : 0.0;
            }
        float f = n / float((2*R+1)*(2*R+1) - 1);
        if (s > 0.5) ns = (f >= uC.z && f <= uC.w) ? 1.0 : 0.0;
        else         ns = (f >= uC.x && f <= uC.y) ? 1.0 : 0.0;
    } else {
        int n = 0;
        for (int j = -1; j <= 1; j++)
            for (int i = -1; i <= 1; i++) {
                if (i == 0 && j == 0) continue;
                ivec2 q = (ip + ivec2(i, j) + res) % res;
                float v = texelFetch(sTD2DInputs[0], q, 0).r;
                n += (abs(v - 1.0) < 0.5) ? 1 : 0;   // state == 1
            }
        if (rule == 1) {                     // Brian's Brain
            if (s < 0.5) ns = (n == 2) ? 1.0 : 0.0;
            else if (s < 1.5) ns = 2.0;
            else ns = 0.0;
        } else if (rule == 2) {              // Wireworld
            if (s < 0.5) ns = 0.0;
            else if (s < 1.5) ns = 2.0;
            else if (s < 2.5) ns = 3.0;
            else ns = (n == 1 || n == 2) ? 1.0 : 3.0;
        } else {                             // Life (B3/S23 via masks) and custom B/S
            int bm = int(uB.x + 0.5), sm = int(uB.y + 0.5);
            if (s > 0.5) ns = ((sm >> n) & 1) == 1 ? 1.0 : 0.0;
            else         ns = ((bm >> n) & 1) == 1 ? 1.0 : 0.0;
        }
    }
    // continuous injection: bright parts of the input keep spawning cells
    if (uE.x > 0.0 && maskAt(uv) && hash2(vec2(ip), uD.w) < uE.x) {
        if (rule == 2) { if (s > 2.5) ns = 1.0; }
        else if (rule == 1) { if (s < 0.5) ns = 1.0; }
        else ns = 1.0;
    }
    float age = (abs(ns - s) < 0.5) ? min(c.g + 1.0, 1000.0) : 0.0;
    float ghost = ns > 0.5 ? 1.0 : c.b * uD.x;
    fragColor = vec4(ns, age, ghost, 1.0);
}
