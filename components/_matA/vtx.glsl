out Vertex { vec3 oP; vec3 oN; vec3 wP; vec3 wN; } vO;
void main(){
  vec3 pos = TDPos();
  vec4 w = TDDeform(pos);
  vO.oP = pos; vO.oN = TDNormal();
  vO.wP = w.xyz; vO.wN = normalize(TDDeformNorm(TDNormal()));
  gl_Position = TDWorldToProj(w);
}
