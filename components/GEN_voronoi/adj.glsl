// Gabriel-graph adjacency (subset of Delaunay edges) between seeds: texel (i,j) = 1 if connected
out vec4 fragColor;
void main(){
    ivec2 ij = ivec2(gl_FragCoord.xy);
    float aspect = uA.w > 0. ? uA.w : 1.777;
    int N = int(uA.y);
    float v = 0.;
    if(ij.x != ij.y && ij.x < N && ij.y < N){
        vec2 a = seedPos(ij.x, aspect), b = seedPos(ij.y, aspect);
        vec2 m = 0.5*(a+b); float r2 = dot(a-b,a-b)*0.25;
        v = 1.;
        for(int k=0;k<128;k++){
            if(k>=N) break;
            if(k==ij.x || k==ij.y) continue;
            vec2 c = seedPos(k, aspect) - m;
            if(dot(c,c) < r2){ v = 0.; break; }
        }
    }
    fragColor = vec4(v,0,0,1);
}
