// in0 = previous dye, in1 = projected velocity, in2 = source image. Advect, dissipate, optionally inject the image.
out vec4 fragColor;
uniform float uDt, uDyeDiss, uInject;
void main(){
    vec2 px = 1.0/vec2(textureSize(sTD2DInputs[0],0)); vec2 uv = vUV.st;
    vec2 v = texture(sTD2DInputs[1], uv).xy;
    vec3 d = texture(sTD2DInputs[0], uv - uDt*v*px).rgb * (1.0-uDyeDiss);
    d = mix(d, texture(sTD2DInputs[2], uv).rgb, clamp(uInject*uDt, 0.0, 1.0));
    fragColor = TDOutputSwizzle(vec4(d, 1.0));
}
