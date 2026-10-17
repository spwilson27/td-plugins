uniform vec4 uP; // x threshold, y softknee
out vec4 fragColor;
void main(){
  vec3 c=texture(sTD2DInputs[0],vUV.st).rgb;
  float b=max(c.r,max(c.g,c.b));
  float knee=uP.x*uP.y+1e-4;
  float s=clamp(b-uP.x+knee,0.,2.*knee); s=s*s/(4.*knee);
  float m=max(s,b-uP.x)/max(b,1e-4);
  fragColor=TDOutputSwizzle(vec4(c*m,1.));
}
