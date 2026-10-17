uniform vec4 uA; // fieldTime, fieldScale, step, fieldType(0 curl,1 angle)
uniform vec4 uB; // trail, hasInput, inputAmt, turbulence
uniform vec4 uC; // active, life(frames), aspect, frame
uniform vec4 uD; // thickness(world), intensity, colorMode, hue
uniform vec4 uE; // mode, lineR, lineG, lineB
uniform vec4 uF; // look(1=mono), accent, isPhase, -
// phase mode: field time travels a circle in the 4th noise dimension -> periodic
float fieldN(vec2 q){ return uF.z > 0.5 ? TDPerlinNoise(vec4(q, 0.6*cos(uA.x), 0.6*sin(uA.x))) : TDPerlinNoise(vec3(q, uA.x)); }
vec2 flowDir(vec2 uv){
    float asp = uC.z;
    vec2 q = vec2(uv.x*asp, uv.y) * uA.y;
    if(uB.y > 0.5){
        vec3 c = texture(sTD2DInputs[1], clamp(uv, 0., 1.)).rgb;
        float l = dot(c, vec3(0.299,0.587,0.114));
        float a = l*6.28318*uB.z + fieldN(q*0.7)*uB.w*3.14159;
        return vec2(cos(a), sin(a));
    }
    if(uA.w < 0.5){
        float e = 0.02;
        float dx = fieldN(q+vec2(e,0.)) - fieldN(q-vec2(e,0.));
        float dy = fieldN(q+vec2(0.,e)) - fieldN(q-vec2(0.,e));
        float fine = uB.w; // turbulence adds a second octave
        if(fine > 0.001){
            vec2 q2 = q*2.3 + 7.1;
            dx += fine*0.5*(fieldN(q2+vec2(e,0.)) - fieldN(q2-vec2(e,0.)));
            dy += fine*0.5*(fieldN(q2+vec2(0.,e)) - fieldN(q2-vec2(0.,e)));
        }
        vec2 v = vec2(dy, -dx);
        return v / max(length(v), 1e-5);
    }
    float a = (fieldN(q) + uB.w*0.5*fieldN(q*2.3+7.1)) * 6.28318 * 1.2;
    return vec2(cos(a), sin(a));
}
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec3 palette(float t){
    t += uD.w;
    return 0.5 + 0.5*cos(6.28318*(vec3(1.0,1.0,1.0)*t + vec3(0.0,0.33,0.67)));
}
