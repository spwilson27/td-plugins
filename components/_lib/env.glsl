// procedural dark-studio equirect environment (softboxes + rim strips); uniforms: uA = (intensity, redAmount, rotation, 0)
out vec4 fragColor;
uniform vec4 uA;
float box(vec2 p, vec2 c, vec2 h, float soft){ vec2 d=abs(p-c)-h; return 1.0-smoothstep(0.0,soft,max(d.x,d.y)); }
void main(){
  vec2 uv = vUV.st; uv.x = fract(uv.x + uA.z);
  float az = uv.x*6.2831853, el = (uv.y-0.5)*3.14159;
  vec3 col = mix(vec3(0.004,0.004,0.005), vec3(0.03,0.032,0.04), smoothstep(-0.6,0.9,el));
  // big key softbox upper front-left
  col += vec3(1.0,0.97,0.92)*2.6*box(vec2(uv.x,uv.y), vec2(0.12,0.72), vec2(0.07,0.12), 0.05);
  // cool strip right
  col += vec3(0.7,0.85,1.0)*1.8*box(uv, vec2(0.62,0.55), vec2(0.012,0.28), 0.02);
  // overhead
  col += vec3(1.0)*1.1*box(uv, vec2(0.4,0.93), vec2(0.18,0.03), 0.03);
  // red accent strip back
  col += vec3(1.0,0.05,0.03)*2.2*uA.y*box(uv, vec2(0.87,0.5), vec2(0.01,0.3), 0.02);
  // floor bounce
  col += vec3(0.05)*smoothstep(0.3,0.0,uv.y);
  fragColor = TDOutputSwizzle(vec4(col*uA.x,1.0));
}
