// default source: moving bone-white silhouette blobs, rings and bars on black (loops on phase)
uniform vec4 uP; // ph
out vec4 fragColor;
#define TAU 6.28318530718
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }
void main(){
  vec2 uv=vUV.st; float asp=uTDOutputInfo.res.z/uTDOutputInfo.res.w;
  vec2 p=(uv-.5)*vec2(asp,1.); float th=uP.x*TAU;
  float v=0.03+0.05*vn(p*6.+vec2(cos(th),sin(th))*.7);
  // metaball silhouette
  float f=0.;
  for(int i=0;i<5;i++){ float fi=float(i);
    vec2 c=vec2(sin(th*(1.+mod(fi,2.))+fi*1.9)*.5, cos(th*(1.+mod(fi+1.,2.))+fi*2.7)*.28);
    float r=.07+.02*fi; vec2 q=p-c; f+=r*r/dot(q,q); }
  float m=smoothstep(.9,1.1,f);
  float tex=.55+.45*vn(p*18.+vec2(sin(th),cos(th)));
  v=mix(v,tex*.95,m);
  v+=.9*smoothstep(.02,0.,abs(f-1.))*.5;                  // bright contour
  // rings + bars
  float d=length(p-vec2(cos(th)*.55,sin(th)*.2));
  v+=.8*smoothstep(.006,0.,abs(d-.12))+.8*smoothstep(.006,0.,abs(d-.17));
  vec2 q=p-vec2(0.,-.3); float a=-th; q=mat2(cos(a),-sin(a),sin(a),cos(a))*q;
  v+=.9*step(abs(q.x),.3)*step(abs(q.y),.012);
  v+=.6*step(abs(q.x),.012)*step(abs(q.y),.2);
  fragColor=TDOutputSwizzle(vec4(vec3(v),1.));
}
