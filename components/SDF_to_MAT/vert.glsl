// proxy-geometry vertex shader: pass object-space position; the fragment shader raymarches inside the proxy
out vec3 vObj;
flat out int vCam;
void main(){
    vec4 w = TDDeform(P);
    vObj = P;
    vCam = TDCameraIndex();
    gl_Position = TDWorldToProj(w);
}
