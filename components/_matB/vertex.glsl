// matB common vertex shader: passes world/object space data (no UVs needed)
out Vtx {
  vec3 wP; vec3 wN; vec3 oP; vec3 oN; vec3 cam;
  vec3 ax; vec3 ay; vec3 az;
  float sh;
} vv;
//DECL
void main(){
  vec3 P = TDPos();
  vec3 N = normalize(TDNormal());
  float sh = 0.0;
  vec3 baseP = P;
//HOOK
  vec4 wp = TDDeform(P);
  vec3 w0 = TDDeform(vec3(0.)).xyz;
  vv.wP = wp.xyz;
  vv.wN = normalize(TDDeformNorm(N));
  vv.oP = baseP;
  vv.oN = N;
  vv.cam = uTDMats[TDCameraIndex()].camInverse[3].xyz;
  vv.ax = TDDeform(vec3(1,0,0)).xyz - w0;
  vv.ay = TDDeform(vec3(0,1,0)).xyz - w0;
  vv.az = TDDeform(vec3(0,0,1)).xyz - w0;
  vv.sh = sh;
  gl_Position = TDWorldToProj(wp);
#ifdef TD_PICKING_ACTIVE
  TDWritePickingValues();
#endif
}
