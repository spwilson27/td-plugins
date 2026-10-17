// Colorize state. Input0 = state. B drives a 4-stop ramp, plus bump lighting.
out vec4 fragColor;
uniform vec3 uC0; uniform vec3 uC1; uniform vec3 uC2; uniform vec3 uC3;
uniform float uContrast;
uniform float uBump;
void main(){
    vec2 px = 1.0 / vec2(textureSize(sTD2DInputs[0], 0));
    vec2 uv = vUV.st;
    float b = texture(sTD2DInputs[0], uv).g;
    float v = clamp(b*uContrast, 0.0, 1.0);
    vec3 col = mix(uC0, uC1, smoothstep(0.0, 0.33, v));
    col = mix(col, uC2, smoothstep(0.33, 0.66, v));
    col = mix(col, uC3, smoothstep(0.66, 1.0, v));
    float bx = texture(sTD2DInputs[0], uv+vec2(px.x,0)).g - texture(sTD2DInputs[0], uv-vec2(px.x,0)).g;
    float by = texture(sTD2DInputs[0], uv+vec2(0,px.y)).g - texture(sTD2DInputs[0], uv-vec2(0,px.y)).g;
    vec3 n = normalize(vec3(-bx*uBump, -by*uBump, 1.0));
    float l = dot(n, normalize(vec3(-0.5,0.6,0.7)));
    col *= 0.65 + 0.55*l;
    col += pow(max(l,0.0), 24.0)*0.15*uBump/6.0;
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
