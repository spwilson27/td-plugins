uniform vec3 uCam; uniform vec3 uLight; uniform vec3 uCol;
in vec3 vNrm; in vec3 vWorld;
layout(location = 0) out vec4 fragColor;
void main(){
    vec3 n = normalize(vNrm); vec3 V = normalize(uCam - vWorld); vec3 L = normalize(uLight);
    float diff = max(dot(n, L), 0.0);
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(n, H), 0.0), 60.0) * 0.4;
    vec3 col = uCol * (0.15 + 0.85 * diff) + vec3(spec);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
