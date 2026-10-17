// LZX / Hydra style oscillator patch that MODULATES THE INPUT. in0 = source image.
uniform vec4 uT;                    // time(s), 0,0,0
uniform vec4 uO0, uO1, uO2;         // x freq, y speed (cycles/s), z rotation deg, w shape (0 sine,1 square,2 saw)
uniform vec4 uM;                    // x modulate, y kaleid segs, z feedback, w colorize
uniform vec4 uN;                    // x scale, y hue, z contrast, w palette
uniform vec4 uQ;                    // x rotspeed (deg/s), y pattern, z echo zoom, w echo rot (deg/tap)
uniform vec4 uR;                    // x echo spacing (s), y displace, z mix mode (0 blend,1 key,2 multiply,3 difference), w gamma
uniform vec4 uS;                    // x key level, y beat pulse, 0, 0
out vec4 fragColor;
const float TAU = 6.2831853;
mat2 rot(float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
float osc(vec2 p, vec4 o, float T, float scale){
    vec2 r = rot(radians(o.z)) * p;
    float ph = o.x * scale * r.x + o.y * T;
    float s = fract(ph);
    if(o.w < .5) return .5 + .5 * sin(TAU * ph);
    if(o.w < 1.5) return smoothstep(.48, .52, s) * smoothstep(1., .96, s);
    return s;
}
vec3 pal(float t, int id){
    t = clamp(t, 0., 1.);
    if(id == 0) return vec3(.93, .91, .85) * t;
    if(id == 1) return mix(vec3(.02, .025, .04), vec3(.75, .82, .9), t) * (.3 + .7 * smoothstep(0., .6, t));
    if(id == 2) return mix(mix(vec3(0.), vec3(.9, .02, .02), smoothstep(0., .55, t)), vec3(.95, .92, .86), smoothstep(.5, 1., t));
    if(id == 3) return .5 + .5 * cos(TAU * (vec3(1.) * t + vec3(.0, .33, .67)));
    return .5 + .5 * cos(TAU * (vec3(1., .8, .6) * t + vec3(.55, .2, .0))) * vec3(1., .5, 1.);
}
vec3 hueRot(vec3 c, float h){
    const vec3 k = vec3(0.57735);
    float ca = cos(h * TAU), sa = sin(h * TAU);
    return c * ca + cross(k, c) * sa + k * dot(k, c) * (1. - ca);
}
vec3 src(vec2 uv){ return texture(sTD2DInputs[0], abs(1. - abs(1. - uv))).rgb; }   // mirrored edges
vec3 scene(vec2 uv, float T){
    float asp = uTDOutputInfo.res.z / uTDOutputInfo.res.w;
    vec2 p = (uv - .5) * vec2(asp, 1.);
    p = rot(radians(uQ.x) * T) * p;
    float seg = uM.y;
    if(seg >= 2.){
        float a = atan(p.y, p.x), r = length(p), w = TAU / seg;
        a = mod(a, w); a = abs(a - w * .5);
        p = r * vec2(cos(a), sin(a));
    }
    float sc = uN.x;
    float A = osc(p, uO0, T, sc);
    vec2 pb = p + (A - .5) * uM.x * vec2(.35, .25);
    float B = osc(pb, uO1, T, sc);
    vec2 pc = p + (B - .5) * uM.x * vec2(-.25, .35) + (A - .5) * uM.x * .15;
    float C = osc(pc, uO2, T, sc);
    float l = mix(abs(A - B), C, .35);
    l = mix(l, A * B, .3);
    l = pow(clamp((l - .5) * uN.z + .5, 0., 1.), uR.w);
    // oscillators displace the input coordinates
    vec2 d = ((A - .5) * vec2(1., .6) + (B - .5) * vec2(-.5, 1.) + (C - .5) * .3) * uR.y * .08;
    vec3 inp;
    float split = uM.w * .6;
    inp = vec3(src(uv + d * (1. + split)).r, src(uv + d).g, src(uv + d * (1. - split)).b);
    // colorise: oscillators rotate the hue of the input
    inp = hueRot(inp, uN.y + (A - B) * uM.w * .5 + uS.y * .15);
    vec3 oc = pal(l, int(uN.w + .5));
    int mm = int(uR.z + .5);
    float pt = uQ.y;
    vec3 col;
    if(mm == 0) col = mix(inp, oc, pt);
    else if(mm == 1){
        float lm = dot(inp, vec3(.299, .587, .114));
        float mask = smoothstep(uS.x - .08, uS.x + .08, lm);
        col = mix(inp, mix(oc, inp, mask), pt);
    }
    else if(mm == 2) col = mix(inp, inp * oc * 2., pt);
    else col = mix(inp, abs(inp - oc), pt);
    return col;
}
void main(){
    vec2 uv = vUV.st;
    float T = uT.x;
    vec3 acc = scene(uv, T);
    float fb = clamp(uM.z, 0., .95);
    vec2 q = uv - .5;
    float w = 1.;
    for(int j = 1; j <= 6; j++){
        w *= fb;
        q = rot(radians(uQ.w)) * q / uQ.z;
        vec2 u2 = q + .5;
        vec3 t = scene(u2, T - float(j) * uR.x) * w;
        float inb = step(0., u2.x) * step(u2.x, 1.) * step(0., u2.y) * step(u2.y, 1.);
        acc = max(acc, t * inb);
    }
    fragColor = TDOutputSwizzle(vec4(acc, 1.));
}
