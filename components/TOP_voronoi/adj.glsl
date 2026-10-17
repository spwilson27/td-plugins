// Gabriel-graph adjacency (subset of Delaunay edges) between seeds: texel (i,j) = 1 if connected
uniform vec4 uA; // count, 0,0,0
out vec4 fragColor;
vec2 seedP(int i){ return texelFetch(sTD2DInputs[0], ivec2(i,0), 0).xy; }
void main(){
    ivec2 ij = ivec2(gl_FragCoord.xy);
    int N = int(uA.x);
    float v = 0.;
    if(ij.x != ij.y && ij.x < N && ij.y < N){
        vec2 a = seedP(ij.x), b = seedP(ij.y);
        vec2 m = 0.5*(a+b); float r2 = dot(a-b,a-b)*0.25;
        v = 1.;
        for(int k=0;k<128;k++){
            if(k>=N) break;
            if(k==ij.x || k==ij.y) continue;
            vec2 c = seedP(k) - m;
            if(dot(c,c) < r2){ v = 0.; break; }
        }
    }
    fragColor = vec4(v,0,0,1);
}
