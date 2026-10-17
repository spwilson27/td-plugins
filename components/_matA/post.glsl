uniform vec4 uPost; // backdrop, exposure, vignette, time
uniform vec4 uRes;
out vec4 fragColor;
float hash12(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.,1.); }
void main(){
  vec2 uv = vUV.st;
  vec4 r = texture(sTD2DInputs[0], uv);
  vec2 q = (uv-0.5)*vec2(uRes.x/uRes.y,1.0);
  // dark studio backdrop: soft pool of light behind subject, floor falloff
  float pool = exp(-dot(q*vec2(0.8,1.3), q*vec2(0.8,1.3))*2.2);
  vec3 bg = vec3(0.006,0.006,0.007) + vec3(0.022,0.023,0.027)*pool*uPost.x;
  bg += vec3(0.02,0.0,0.0)*uPost.x*smoothstep(0.0,-0.5,q.y)*pool;
  vec3 col = r.rgb + bg*(1.0-r.a);
  col *= uPost.y;
  col = aces(col);
  col = pow(col, vec3(1.0/2.2));
  float v = 1.0 - uPost.z*dot(q,q)*0.9;
  col *= clamp(v,0.,1.);
  col += (hash12(uv*uRes.xy + fract(uPost.w)*91.0)-0.5)/200.0;
  fragColor = TDOutputSwizzle(vec4(col,1.0));
}
