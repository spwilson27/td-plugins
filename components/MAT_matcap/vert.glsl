out vec3 vNrmView;
void main(){
    vec4 w = TDDeform(P);
    vec3 nw = normalize(TDDeformNorm(N));
    vNrmView = mat3(uTDMats[TDCameraIndex()].cam) * nw;
    gl_Position = TDWorldToProj(w);
}
