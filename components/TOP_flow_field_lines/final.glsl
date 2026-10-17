uniform vec4 uA; // exposure, composite(0 over input,1 add,2 on background), inputDim, 0
uniform vec3 uBg;
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec3 acc = texture(sTD2DInputs[0], uv).rgb;
    vec3 src = texture(sTD2DInputs[1], uv).rgb;
    vec3 t = 1. - exp(-acc*uA.x);
    float cov = max(t.r, max(t.g, t.b));
    int m = int(uA.y + 0.5);
    vec3 res;
    if(m == 0) res = src*uA.z*(1.-cov) + t;
    else if(m == 1) res = src + t;
    else res = uBg*(1.-cov) + t;
    fragColor = TDOutputSwizzle(vec4(res, 1.));
}
