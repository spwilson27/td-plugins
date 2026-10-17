// iridescent_material: vertex stage
out vec3 vWPos;
out vec3 vWNrm;
out vec2 vTex;
out vec3 vCam;
void main(){
  vec4 wp = TDDeform(P);
  gl_Position = TDWorldToProj(wp);
  vWPos = wp.xyz;
  vWNrm = normalize(TDDeformNorm(N));
  vTex = uv[0].st;
  vCam = uTDMats[TDCameraIndex()].camInverse[3].xyz;
}
