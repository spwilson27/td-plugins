// Procedural matcap generator. uIdx.x = matcap index (0..7) or -1 for a 4x2 contact sheet.
uniform vec4 uIdx;
out vec4 fragColor;

vec3 env(vec3 r){
    float up = r.y * 0.5 + 0.5;
    vec3 c = mix(vec3(0.04, 0.04, 0.05), vec3(0.55, 0.58, 0.64), smoothstep(0.20, 1.0, up));
    c += vec3(0.9) * exp(-pow((r.y - 0.04) * 7.0, 2.0)) * 0.35;                  // horizon glow
    c += vec3(5.0) * smoothstep(0.86, 0.92, dot(r, normalize(vec3(-0.55, 0.75, 0.45))));   // key softbox
    c += vec3(2.2, 2.3, 2.6) * smoothstep(0.94, 0.965, dot(r, normalize(vec3(0.85, 0.20, 0.45)))); // rim strip
    c += vec3(1.2) * smoothstep(0.93, 0.95, dot(r, normalize(vec3(0.0, -0.6, 0.8)))) ;   // floor kicker
    return c;
}
vec3 tonemap(vec3 c){ return c / (1.0 + c * 0.35) ; }

vec3 matcap(int idx, vec3 n){
    vec3 v = vec3(0.0, 0.0, 1.0);
    vec3 L = normalize(vec3(-0.5, 0.6, 0.65));
    vec3 r = reflect(-v, n);
    float nl = dot(n, L);
    float diff = max(nl, 0.0);
    float wrap = clamp((nl + 0.5) / 1.5, 0.0, 1.0);
    float fr = pow(1.0 - clamp(n.z, 0.0, 1.0), 3.0);
    vec3 H = normalize(L + v);
    float nh = max(dot(n, H), 0.0);
    vec3 c = vec3(0.0);
    if (idx == 0) {          // clay
        c = vec3(0.60, 0.56, 0.51) * (0.10 + 0.95 * wrap * wrap) + vec3(0.5, 0.52, 0.58) * fr * 0.18;
    } else if (idx == 1) {   // chrome
        c = tonemap(env(r)) * vec3(0.95, 0.97, 1.0);
    } else if (idx == 2) {   // pearl
        vec3 irid = 0.5 + 0.5 * cos(6.2831853 * (fr * 1.4 + n.y * 0.25 + vec3(0.0, 0.33, 0.67)));
        c = vec3(0.86, 0.85, 0.84) * (0.30 + 0.70 * wrap) + tonemap(env(r)) * 0.30
          + irid * fr * 0.55 + vec3(1.0) * pow(nh, 90.0) * 0.6;
    } else if (idx == 3) {   // toon
        float b = floor(clamp(diff, 0.0, 0.999) * 3.0) / 3.0;
        c = mix(vec3(0.09, 0.07, 0.12), vec3(0.97, 0.88, 0.72), b + 0.1);
        c += step(0.93, nh) * 0.5;
        if (n.z < 0.28) c = vec3(0.0);
    } else if (idx == 4) {   // jade
        c = vec3(0.06, 0.42, 0.28) * (0.25 + 0.95 * wrap) + vec3(0.25, 0.85, 0.55) * pow(1.0 - n.z, 2.0) * 0.30
          + vec3(1.0) * pow(nh, 70.0) * 0.8 + tonemap(env(r)) * 0.10;
    } else if (idx == 5) {   // gold
        float f = 0.75 + 0.25 * fr;
        c = tonemap(env(r)) * vec3(1.0, 0.76, 0.32) * f * 1.5;
    } else if (idx == 6) {   // bone
        c = vec3(0.88, 0.84, 0.74) * (0.18 + 0.85 * wrap) + vec3(0.4, 0.38, 0.34) * fr * 0.2 + vec3(0.7) * pow(nh, 18.0) * 0.12;
    } else {                 // black glass
        c = vec3(0.006) + tonemap(env(r)) * (0.035 + 0.95 * fr) + vec3(1.0) * pow(nh, 220.0);
    }
    return c;
}

void main(){
    vec2 uv = vUV.st;
    int idx = int(uIdx.x + 0.5);
    float inDisc = 1.0;
    if (uIdx.x < -0.5) {
        vec2 t = vec2(uv.x * 4.0, uv.y * 2.0);
        idx = int(floor(t.x)) + 4 * (1 - int(floor(t.y)));
        uv = fract(t);
    }
    vec2 p = uv * 2.0 - 1.0;
    float rr = length(p);
    vec3 n = vec3(p, sqrt(max(0.0, 1.0 - rr * rr)));
    if (rr > 1.0) { n = vec3(p / rr, 0.0); if (uIdx.x < -0.5) inDisc = 0.0; }
    vec3 c = matcap(clamp(idx, 0, 7), normalize(n)) * inDisc;
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
