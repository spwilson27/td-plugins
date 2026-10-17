out vec3 vWorld;
out vec3 vNrm;
out vec3 vCam;
void main(){
    vec4 w = TDDeform(P);
    vWorld = w.xyz;
    vNrm = normalize(TDDeformNorm(N));
    vCam = uTDMats[TDCameraIndex()].camInverse[3].xyz;
    gl_Position = TDWorldToProj(w);
}
