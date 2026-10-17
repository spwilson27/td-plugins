uniform vec4 uA; // fade, active, exposure, 0
out vec4 fragColor;
void main(){
    vec4 prev = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    vec3 nw = texelFetch(sTD2DInputs[1], ivec2(gl_FragCoord.xy), 0).rgb;
    vec3 acc = (uA.y > 0.5) ? prev.rgb*uA.x + nw*(1.-uA.x)*4.0 : prev.rgb;
    fragColor = vec4(acc, 1.);
}
