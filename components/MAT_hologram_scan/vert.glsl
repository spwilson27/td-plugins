out vec3 vWorld;
out vec3 vNrm;
out vec3 vObj;
out vec2 vUV;
out vec3 vCam;
void main(){
    vec4 w = TDDeform(P);
    vWorld = w.xyz;
    vNrm = normalize(TDDeformNorm(N));
    vObj = P;
    vCam = uTDMats[TDCameraIndex()].camInverse[3].xyz;
    vUV = uv[0].st;
    gl_Position = TDWorldToProj(w);
}
