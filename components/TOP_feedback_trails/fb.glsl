// in0 = previous frame (feedback), in1 = source
uniform vec4 uXf;     // x scale, y rotate(rad/frame), z tx, w ty
uniform vec4 uCol;    // x hue deg/frame, y decay, z inject, w active
uniform vec4 uNz;     // x amount, y scale, z speed*time, w blend mode
out vec4 fragColor;
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }
vec3 hueRot(vec3 c,float a){
  const mat3 toY=mat3(0.299,0.596,0.211,0.587,-0.274,-0.523,0.114,-0.322,0.312);
  const mat3 fromY=mat3(1.,1.,1.,0.956,-0.272,-1.106,0.621,-0.647,1.703);
  vec3 y=toY*c; float ca=cos(a),sa=sin(a);
  y.yz=mat2(ca,-sa,sa,ca)*y.yz; return fromY*y; }
void main(){
  vec2 uv=vUV.st;
  vec4 src=texture(sTD2DInputs[1],uv);
  vec4 prev=texture(sTD2DInputs[0],uv);
  if(uCol.w<.5){ fragColor=TDOutputSwizzle(prev); return; }
  float asp=uTDOutputInfo.res.z/uTDOutputInfo.res.w;
  vec2 p=uv-.5; p.x*=asp;
  p-=vec2(uXf.z*asp,uXf.w);
  float ca=cos(uXf.y),sa=sin(uXf.y);
  p=mat2(ca,-sa,sa,ca)*p;
  p/=max(uXf.x,1e-3);
  vec2 q=vec2(p.x/asp,p.y)+.5;
  vec2 no=vec2(uNz.z);
  vec2 n=vec2(vn(q*uNz.y+no),vn(q*uNz.y+no+31.7))-.5;
  q+=n*uNz.x*.03;
  vec4 pv=texture(sTD2DInputs[0],q);
  pv.rgb=hueRot(pv.rgb,radians(uCol.x))*uCol.y;
  vec3 s=src.rgb*uCol.z;
  float luma=dot(src.rgb,vec3(.299,.587,.114));
  vec3 r;
  if(uNz.w<.5){ float m=smoothstep(.03,.25,luma)*src.a; r=mix(pv.rgb,s,m); }
  else if(uNz.w<1.5) r=pv.rgb+s;
  else r=max(pv.rgb,s);
  fragColor=TDOutputSwizzle(vec4(max(r,0.),1.));
}
