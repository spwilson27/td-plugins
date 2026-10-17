// Seed table, 128 x 2 (rgba32float).  row 0: xy = seed position (x scaled by aspect), z = id hash
// row 1: rgb = input colour sampled at the seed, a = luminance.  Positions may be steered by the input.
uniform vec4 uA; // time, count, jitter, seed
uniform vec4 uB; // motion, density mode (0 uniform 1 bright 2 dark 3 edges), density amount, 0
out vec4 fragColor;
float hash11(float n){ return fract(sin(n*127.1+311.7)*43758.5453); }
vec2 hash21(float n){ return vec2(hash11(n), hash11(n+17.31)); }
float lum(vec3 c){ return dot(c, vec3(.299,.587,.114)); }
vec3 smp(vec2 uv){ return texture(sTD2DInputs[0], clamp(uv, 0.002, 0.998)).rgb; }
float weightAt(vec2 c){
    int m = int(uB.y + 0.5);
    if(m == 0) return 0.;
    if(m == 1) return lum(smp(c));
    if(m == 2) return 1. - lum(smp(c));
    float e = 0.006;
    float gx = lum(smp(c+vec2(e,0.))) - lum(smp(c-vec2(e,0.)));
    float gy = lum(smp(c+vec2(0.,e))) - lum(smp(c-vec2(0.,e)));
    return clamp(length(vec2(gx,gy))*5., 0., 1.);
}
vec2 seedUV(int i, float aspect){
    float fi = float(i);
    float N = max(uA.y, 1.);
    float best = -1e9; vec2 bp = vec2(.5);
    for(int k=0;k<10;k++){
        vec2 c = hash21(fi*7.3 + float(k)*1.91 + uA.w*13.7);
        float sc = uB.z*6.*weightAt(c) + hash11(fi*3.1 + float(k)*5.7 + uA.w);
        if(sc > best){ best = sc; bp = c; }
    }
    float gx = ceil(sqrt(N*aspect)); float gy = ceil(N/gx);
    vec2 g = (vec2(mod(fi, gx), floor(fi/gx)) + 0.5) / vec2(gx, gy);
    vec2 b = mix(g, bp, uA.z);
    float t = uA.x;
    vec2 h = hash21(fi*3.7 + 5.);
    vec2 o = vec2(sin(t*(0.4+h.x) + h.y*6.283) + 0.5*sin(t*((1.1+h.y)*1.7) + h.x*9.),
                  cos(t*(0.35+h.y) + h.x*6.283) + 0.5*sin(t*((0.9+h.x)*1.9) + h.y*7.));
    return clamp(b + o*0.05*uB.x, 0.005, 0.995);
}
void main(){
    ivec2 ij = ivec2(gl_FragCoord.xy);
    vec2 sz = vec2(textureSize(sTD2DInputs[0], 0));
    float aspect = sz.x/sz.y;
    vec4 r = vec4(0.);
    if(ij.x < int(uA.y)){
        vec2 p = seedUV(ij.x, aspect);
        if(ij.y == 0){
            r = vec4(p.x*aspect, p.y, hash11(float(ij.x)*1.37 + uA.w), 1.);
        } else {
            float rad = 0.35/sqrt(max(uA.y,1.));
            vec3 c = vec3(0.); float ws = 0.;
            for(int a=-1;a<=1;a++) for(int b=-1;b<=1;b++){
                float w = (a==0&&b==0) ? 2. : 1.;
                c += w*smp(p + vec2(float(a)*rad/aspect, float(b)*rad)); ws += w;
            }
            c /= ws;
            r = vec4(c, lum(c));
        }
    }
    fragColor = r;
}
