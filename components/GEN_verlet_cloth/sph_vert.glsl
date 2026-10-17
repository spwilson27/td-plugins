uniform vec4 uS;
out vec3 vNrm; out vec3 vWorld;
void main(){
    vec3 p = P * uS.w + uS.xyz;
    vNrm = normalize(N);
    vWorld = p;
    gl_Position = TDWorldToProj(vec4(p, 1.0));
}
