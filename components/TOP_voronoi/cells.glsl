// Per-pixel cell data (rgba32float): r = nearest seed index, g = second-nearest (across the nearest border),
// b = distance to nearest seed, a = distance to the cell border (height units)
uniform vec4 uA; // count, 0,0,0
out vec4 fragColor;
vec2 seedP(int i){ return texelFetch(sTD2DInputs[1], ivec2(i,0), 0).xy; }
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    float aspect = res.x/res.y;
    vec2 p = vec2(vUV.s*aspect, vUV.t);
    int N = int(clamp(uA.x, 2., 128.));
    float d1 = 1e9; int i1 = 0;
    for(int i=0;i<128;i++){
        if(i>=N) break;
        float d = distance(p, seedP(i));
        if(d < d1){ d1 = d; i1 = i; }
    }
    vec2 s1 = seedP(i1);
    float bd = 1e9; int i2 = i1;
    for(int j=0;j<128;j++){
        if(j>=N) break;
        if(j==i1) continue;
        vec2 sj = seedP(j);
        float b = dot(0.5*(s1+sj) - p, normalize(sj - s1));
        if(b < bd){ bd = b; i2 = j; }
    }
    fragColor = vec4(float(i1), float(i2), d1, bd);
}
