uniform vec4 uP; // x width px, y threshold, z softness, w colour weight
out vec4 fragColor;
vec3 S(vec2 uv){ return clamp(texture(sTD2DInputs[0],uv).rgb,0.,1.); }
float lu(vec3 c){ return dot(c,vec3(.299,.587,.114)); }
void main(){
  vec2 uv=vUV.st; vec2 d=uTDOutputInfo.res.xy*uP.x;
  vec3 a=S(uv+vec2(-d.x,-d.y)),b=S(uv+vec2(0.,-d.y)),c=S(uv+vec2(d.x,-d.y));
  vec3 e=S(uv+vec2(-d.x,0.)),g=S(uv+vec2(d.x,0.));
  vec3 h=S(uv+vec2(-d.x,d.y)),i=S(uv+vec2(0.,d.y)),j=S(uv+vec2(d.x,d.y));
  vec3 gx=(c+2.*g+j)-(a+2.*e+h);
  vec3 gy=(h+2.*i+j)-(a+2.*b+c);
  float gl=length(vec2(lu(gx),lu(gy)));
  float gc=length(vec2(length(gx),length(gy)))*.5;
  float m=mix(gl,gc,uP.w);
  float ed=smoothstep(uP.y,uP.y+max(uP.z,.001),m);
  fragColor=TDOutputSwizzle(vec4(vec3(ed),1.));
}
