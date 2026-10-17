// Velocity advection + dissipation + vorticity confinement + forces (emitter splats and in1 image).
// in0 = previous velocity, in1 = curl, in2 = in1 image (optional)
out vec4 fragColor;
uniform float uDt, uVelDiss, uVort, uPh, uAspect, uHasIn, uInVel;
uniform float uEmitters, uSplatSize, uForce, uEmitCyc, uResScale;
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
float lum(vec3 c){ return dot(c, vec3(0.299,0.587,0.114)); }
void main(){
    vec2 px = 1.0/vec2(textureSize(sTD2DInputs[0],0)); vec2 uv = vUV.st;
    vec2 v = texture(sTD2DInputs[0], uv).xy;
    vec2 nv = texture(sTD2DInputs[0], uv - uDt*v*px).xy * (1.0-uVelDiss);
    // vorticity confinement
    float cL = abs(texture(sTD2DInputs[1], uv-vec2(px.x,0)).x), cR = abs(texture(sTD2DInputs[1], uv+vec2(px.x,0)).x);
    float cB = abs(texture(sTD2DInputs[1], uv-vec2(0,px.y)).x), cT = abs(texture(sTD2DInputs[1], uv+vec2(0,px.y)).x);
    float w = texture(sTD2DInputs[1], uv).x;
    vec2 N = 0.5*vec2(cR-cL, cT-cB); N /= (length(N)+1e-6);
    nv += uDt * uVort * w * vec2(N.y, -N.x);
    // emitters
    for (int i=0;i<6;i++){
        if (float(i) >= uEmitters) break;
        vec2 dir; vec2 p = emitPos(i, uPh, uEmitCyc, dir);
        vec2 d = (uv-p)*vec2(uAspect,1.0);
        float wgt = exp(-dot(d,d)/(uSplatSize*uSplatSize));
        nv += uDt * dir * uForce * uResScale * wgt;
    }
    if (uHasIn > 0.5 && uInVel > 0.0){
        float l  = lum(texture(sTD2DInputs[2], uv-vec2(px.x,0)).rgb), r = lum(texture(sTD2DInputs[2], uv+vec2(px.x,0)).rgb);
        float b  = lum(texture(sTD2DInputs[2], uv-vec2(0,px.y)).rgb), tt = lum(texture(sTD2DInputs[2], uv+vec2(0,px.y)).rgb);
        vec2 g = vec2(r-l, tt-b);              // luminance gradient -> flow runs along image edges
        nv += uDt * uInVel * uResScale * vec2(-g.y, g.x) * 4.0;
    }
    fragColor = TDOutputSwizzle(vec4(nv, 0.0, 1.0));
}
