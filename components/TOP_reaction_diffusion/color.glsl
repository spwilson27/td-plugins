// Stylise: input0 = state (R=A, G=B), input1 = image.
out vec4 fragColor;
uniform vec3 uC0; uniform vec3 uC1; uniform vec3 uC2; uniform vec3 uC3;
uniform vec4 uStyle;   // x mode, y strength, z contrast, w bump
vec3 ramp(float v){
    vec3 col = mix(uC0, uC1, smoothstep(0.0, 0.33, v));
    col = mix(col, uC2, smoothstep(0.33, 0.66, v));
    return mix(col, uC3, smoothstep(0.66, 1.0, v));
}
void main(){
    vec2 px = 1.0 / vec2(textureSize(sTD2DInputs[0], 0));
    vec2 uv = vUV.st;
    int mode = int(uStyle.x + 0.5);
    float S = uStyle.y;
    float b = texture(sTD2DInputs[0], uv).g;
    float p = clamp(b*uStyle.z, 0.0, 1.0);
    float bx = texture(sTD2DInputs[0], uv+vec2(px.x,0)).g - texture(sTD2DInputs[0], uv-vec2(px.x,0)).g;
    float by = texture(sTD2DInputs[0], uv+vec2(0,px.y)).g - texture(sTD2DInputs[0], uv-vec2(0,px.y)).g;
    vec3 n = normalize(vec3(-bx*uStyle.w, -by*uStyle.w, 1.0));
    float l = dot(n, normalize(vec3(-0.5,0.6,0.7)));
    vec3 col;
    if (mode == 5) {            // warp: refract the image through the B gradient
        vec2 d = vec2(bx, by) * uStyle.w * S * 0.04;
        col = texture(sTD2DInputs[1], uv - d).rgb;
    } else {
        vec3 img = texture(sTD2DInputs[1], uv).rgb;
        if (mode == 0)      col = mix(img, ramp(p), clamp(p*S, 0.0, 1.0));                 // tint
        else if (mode == 1) col = img * mix(vec3(1.0), uC3, clamp(p*S, 0.0, 1.0));         // multiply
        else if (mode == 2) col = img * (1.0 + S*1.2*(l - 0.5)) + pow(max(l,0.0), 24.0)*0.25*S;   // emboss
        else if (mode == 3) col = ramp(p) * (0.65 + 0.55*l) + pow(max(l,0.0), 24.0)*0.15*uStyle.w/6.0;   // ramp
        else                col = vec3(p);                                                   // field
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
