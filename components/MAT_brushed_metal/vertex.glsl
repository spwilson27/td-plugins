uniform vec4 uB0; // Direction mode (0 x,1 y,2 z,3 radial,4 circular), ...
out Vertex { vec3 oP; vec3 oN; vec3 wP; vec3 wN; vec3 wT; vec3 oT; } vO;
vec3 brushDir(vec3 p, vec3 n){
  int m = int(uB0.x + 0.5);
  vec3 d;
  if (m == 0) d = vec3(1,0,0);
  else if (m == 1) d = vec3(0,1,0);
  else if (m == 2) d = vec3(0,0,1);
  else if (m == 3) d = vec3(p.x, 0.0, p.z);            // radial spokes about object Y
  else d = vec3(p.z, 0.0, -p.x);                        // circular rings about object Y
  d -= n*dot(d,n);
  float l = length(d);
  if (l < 1e-4){ d = cross(n, abs(n.y) < 0.9 ? vec3(0,1,0) : vec3(1,0,0)); l = length(d); }
  return d / l;
}
void main(){
  vec3 pos = TDPos();
  vec3 n = normalize(TDNormal());
  vec4 w = TDDeform(pos);
  vec3 t = brushDir(pos, n);
  vO.oP = pos; vO.oN = n; vO.oT = t;
  vO.wP = w.xyz; vO.wN = normalize(TDDeformNorm(n));
  vO.wT = normalize(TDDeform(pos + t*0.01).xyz - w.xyz);
  gl_Position = TDWorldToProj(w);
}
