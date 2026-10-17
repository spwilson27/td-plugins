out vec3 vWorld;
out vec3 vNrmW;
out vec3 vObj;
out vec3 vNrmO;
out vec3 vCam;
void main(){
    vec4 w = TDDeform(P);
    vWorld = w.xyz;
    vNrmW = normalize(TDDeformNorm(N));
    vObj = P;
    vNrmO = normalize(N);
    vCam = uTDMats[TDCameraIndex()].camInverse[3].xyz;
    gl_Position = TDWorldToProj(w);
}
