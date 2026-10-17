// jelly_material: vertex jiggle (periodic in phase) + analytic-ish normal perturbation
uniform vec4 uJig; // amplitude, frequency, cycles (int per loop), phase(0..1+)
out vec3 vWPos;
out vec3 vWNrm;
out vec3 vObj;
out vec3 vCam;
#define TAU 6.28318530718
float jig(vec3 p){
  float th=uJig.w*TAU*max(floor(uJig.z+.5),0.);
  float f=uJig.y;
  return uJig.x*( sin(p.x*f+th*1.)*sin(p.y*f*.9-th*2.)*.6
                + sin(p.z*f*1.3+p.x*f*.5+th*3.)*.4 );
}
void main(){
  vec3 n=normalize(N);
  vec3 p=P;
  float d=jig(p);
  vec3 p2=p+n*d;
  // normal perturbation from finite-difference gradient
  float e=.01;
  vec3 g=vec3(jig(p+vec3(e,0,0))-jig(p-vec3(e,0,0)),jig(p+vec3(0,e,0))-jig(p-vec3(0,e,0)),jig(p+vec3(0,0,e))-jig(p-vec3(0,0,e)))/(2.*e);
  g-=dot(g,n)*n;
  vec3 n2=normalize(n-g);
  vec4 wp=TDDeform(p2);
  gl_Position=TDWorldToProj(wp);
  vWPos=wp.xyz;
  vWNrm=normalize(TDDeformNorm(n2));
  vObj=p2;
  vCam=uTDMats[TDCameraIndex()].camInverse[3].xyz;
}
