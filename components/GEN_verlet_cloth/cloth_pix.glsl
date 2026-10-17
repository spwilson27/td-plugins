uniform vec3 uC1; uniform vec3 uC2; uniform vec3 uCam; uniform vec3 uLight;
uniform float uCheck;
in vec3 vNrm; in vec3 vWorld; in vec2 vG;
layout(location = 0) out vec4 fragColor;
void main(){
    vec3 V = normalize(uCam - vWorld);
    vec3 n = normalize(vNrm);
    if (dot(n, V) < 0.0) n = -n;
    vec2 cell = floor(vG * uCheck);
    float chk = mod(cell.x + cell.y, 2.0);
    vec3 base = mix(uC1, uC2, chk);
    vec3 L = normalize(uLight);
    float diff = max(dot(n, L), 0.0);
    float wrap = 0.5 + 0.5 * dot(n, L);
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(n, H), 0.0), 40.0) * 0.25;
    float rim = pow(1.0 - max(dot(n, V), 0.0), 3.0) * 0.15;
    vec3 col = base * (0.18 + 0.55 * diff + 0.3 * wrap) + vec3(spec + rim);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
