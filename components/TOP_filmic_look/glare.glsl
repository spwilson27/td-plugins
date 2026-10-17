// horizontal anamorphic streak of the bright-pass (exponentially spaced taps)
uniform vec4 uP; // x length (uv), y tint r, z g, w b
out vec4 fragColor;
void main(){
  vec2 uv=vUV.st; vec3 acc=vec3(0.); float ws=0.;
  for(int i=-32;i<=32;i++){
    float f=float(i)/32.; float a=abs(f);
    float off=sign(f)*a*a*uP.x;          // denser near centre
    float wgt=exp(-a*3.2);
    acc+=texture(sTD2DInputs[0],uv+vec2(off,0.)).rgb*wgt; ws+=wgt;
  }
  acc/=ws;
  fragColor=TDOutputSwizzle(vec4(acc*uP.yzw*4.,1.));
}
