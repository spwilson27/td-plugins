// Integrate positions. in0 = previous positions, in1 = new velocities.
out vec4 fragColor;
uniform float uDt, uBound, uWrap, uObsOn, uObsR, uCount;
uniform vec3 uObsPos;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    int me = ip.y * textureSize(sTD2DInputs[0],0).x + ip.x;
    vec3 p = texelFetch(sTD2DInputs[0], ip, 0).xyz;
    vec3 v = texelFetch(sTD2DInputs[1], ip, 0).xyz;
    p += v * uDt;
    if (uWrap > 0.5) p = mod(p + uBound, 2.0*uBound) - uBound;
    else p = clamp(p, vec3(-uBound), vec3(uBound));
    if (uObsOn > 0.5) {
        vec3 od = p - uObsPos; float dist = length(od);
        if (dist < uObsR) p = uObsPos + od / max(dist, 1e-4) * uObsR;
    }
    fragColor = TDOutputSwizzle(vec4(p, float(me) < uCount ? 1.0 : 0.0));
}
