// Per-boid colour from velocity. in0 = velocity. Output rgb colour, a = speed fraction.
out vec4 fragColor;
uniform vec3 uColA, uColB;
uniform float uMaxSpeed;
void main(){
    vec3 v = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0).xyz;
    float sp = clamp(length(v)/max(uMaxSpeed,1e-3), 0.0, 1.0);
    vec3 dir = normalize(v + 1e-5) * 0.5 + 0.5;
    vec3 base = mix(uColA, uColB, sp);
    fragColor = TDOutputSwizzle(vec4(mix(base, base*(0.4+1.2*dir), 0.55), sp));
}
