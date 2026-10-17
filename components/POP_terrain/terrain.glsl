// POP_terrain: displace points along their normal by a heightmap sampled at the point's texcoord.
// uA: height, scroll (v offset), style (0 smooth,1 ridged,2 terraced), terraces
// uB: look (0 original,1 mono), accent, source-is-noise (contrast boost), 0
uniform vec4 uA, uB;
void main(){
  const uint id = TDIndex(); if(id >= TDNumElements()) return;
  vec3 p = TDIn_P();
  vec3 n = normalize(TDIn_N() + vec3(1e-6));
  vec2 uv = TDIn_Tex().xy;
  uv.y += uA.y;
  float h = dot(texture(uTex, uv).rgb, vec3(0.299, 0.587, 0.114));
  if(uB.z > 0.5) h = clamp((h - 0.5) * 1.8 + 0.5, 0.0, 1.0);
  if(uA.z > 0.5 && uA.z < 1.5) { h = 1.0 - abs(2.0*h - 1.0); h = h*h; }
  if(uA.z > 1.5) { float k = max(uA.w, 1.0); float f = h*k; h = (floor(f) + smoothstep(0.35, 0.65, fract(f))) / k; }
  P[id] = p + n * h * uA.x;
  vec3 col;
  float t = clamp(h, 0.0, 1.0);
  if(uB.x < 0.5){
    col = mix(vec3(0.10, 0.30, 0.55), vec3(0.95, 0.9, 0.8), smoothstep(0.0, 0.8, t));
    col = mix(col, vec3(1.0, 0.1, 0.05), uB.y * smoothstep(0.75, 1.0, t));
  } else {
    col = vec3(0.2 + 0.8*t);
    col = mix(col, vec3(1.0, 0.1, 0.05), uB.y * smoothstep(0.75, 1.0, t));
  }
  Color[id] = vec4(col * (0.35 + 0.9*t), 1.0);
}
