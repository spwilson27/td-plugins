// Lucas-Kanade optical flow (iterative, warped). in0 current, in1 previous, in2 previous flow (temporal smoothing)
uniform vec4 uP; // x regularisation  y temporal smooth  z iterations (1..3)  w max px per frame
out vec4 fragColor;
float lu(vec3 c){ return dot(c,vec3(.299,.587,.114)); }
float C(vec2 p){ return lu(texture(sTD2DInputs[0],p).rgb); }
float P(vec2 p){ return lu(texture(sTD2DInputs[1],p).rgb); }
void main(){
  vec2 uv=vUV.st; vec2 px=uTDOutputInfo.res.xy;
  vec2 g=vec2(0.);                       // accumulated flow in uv
  int iters=int(uP.z+.5);
  for(int it=0;it<3;it++){
    if(it>=iters) break;
    float sxx=0.,sxy=0.,syy=0.,bx=0.,by=0.;
    for(int j=-3;j<=3;j++) for(int i=-3;i<=3;i++){
      vec2 p=uv+vec2(i,j)*px;
      vec2 q=p-g;                         // matching location in previous frame
      float w=1./(1.+.25*float(i*i+j*j));
      float gx=.25*(C(p+vec2(px.x,0.))-C(p-vec2(px.x,0.))+P(q+vec2(px.x,0.))-P(q-vec2(px.x,0.)));
      float gy=.25*(C(p+vec2(0.,px.y))-C(p-vec2(0.,px.y))+P(q+vec2(0.,px.y))-P(q-vec2(0.,px.y)));
      float r=C(p)-P(q);
      sxx+=w*gx*gx; sxy+=w*gx*gy; syy+=w*gy*gy; bx+=w*gx*r; by+=w*gy*r;
    }
    float l=uP.x; sxx+=l; syy+=l;
    float det=sxx*syy-sxy*sxy;
    vec2 dv=-vec2(syy*bx-sxy*by,-sxy*bx+sxx*by)/det;   // texels
    dv=clamp(dv,-uP.w,uP.w);
    g+=dv*px;
  }
  vec2 pf=texture(sTD2DInputs[2],uv).xy;
  g=mix(g,pf,uP.y);
  fragColor=vec4(g,length(g/px),1.);
}
