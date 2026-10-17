// in0 = previous dye, in1 = projected velocity, in2 = in1 image (optional)
out vec4 fragColor;
uniform float uDt, uDyeDiss, uPh, uAspect, uHasIn, uInDens;
uniform float uEmitters, uSplatSize, uDensity, uEmitCyc, uHueCyc;
vec3 hsv(float h){ return clamp(abs(mod(h*6.0+vec3(0,4,2),6.0)-3.0)-1.0,0.0,1.0); }
const float KX[6] = float[6](1.,1.,2.,1.,2.,3.);
const float KY[6] = float[6](1.,2.,1.,3.,1.,2.);
const float TAU = 6.2831853;
// loop-periodic emitter path: integer Lissajous cycles per loop (cyc = round(Emitterspeed))
vec2 emitPos(int i, float ph, float cyc, out vec2 dir){
    float fi = float(i);
    vec2 A = vec2(0.34, 0.30);
    float a = TAU*KX[i]*cyc*ph + fi*2.1, b = TAU*KY[i]*cyc*ph + fi*2.73;
    dir = normalize(A*vec2(KX[i]*cos(a), -KY[i]*sin(b)) + 1e-5);
    return vec2(0.5) + A*vec2(sin(a), cos(b));
}
void main(){
    vec2 px = 1.0/vec2(textureSize(sTD2DInputs[0],0)); vec2 uv = vUV.st;
    vec2 v = texture(sTD2DInputs[1], uv).xy;
    vec3 d = texture(sTD2DInputs[0], uv - uDt*v*px).rgb * (1.0-uDyeDiss);
    for (int i=0;i<6;i++){
        if (float(i) >= uEmitters) break;
        vec2 dr; vec2 p = emitPos(i, uPh, uEmitCyc, dr);
        vec2 q = (uv-p)*vec2(uAspect,1.0);
        float wgt = exp(-dot(q,q)/(uSplatSize*uSplatSize));
        vec3 col = hsv(fract(uPh*uHueCyc + float(i)/max(uEmitters,1.0)));
        d += uDt * uDensity * col * wgt;
    }
    if (uHasIn > 0.5 && uInDens > 0.0) d += uDt * uInDens * texture(sTD2DInputs[2], uv).rgb * 0.02;
    fragColor = TDOutputSwizzle(vec4(d, 1.0));
}
