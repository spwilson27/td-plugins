// Look post-process. in0 = rendered image.  uL: x=look(0 original,1 mono) y=accent z=accent mode(0 warm,1 peak) w=gain
out vec4 fragColor;
uniform vec4 uL;
void main(){
    vec4 s = texture(sTD2DInputs[0], vUV.st);
    vec3 c = s.rgb;
    if (uL.x < 0.5) { fragColor = TDOutputSwizzle(s); return; }
    float l = dot(max(c, 0.0), vec3(0.299, 0.587, 0.114)) * uL.w;
    float g = 1.0 - exp(-l * 1.6);            // soft shoulder so highlights stay bone, not clipped
    g = smoothstep(0.015, 1.0, g);
    vec3 bone = vec3(0.93, 0.91, 0.86);
    vec3 col = bone * g;
    col *= mix(vec3(0.82, 0.84, 0.88), vec3(1.0), g);   // cool grey in the lows, bone in the highs
    if (uL.y > 0.5) {
        float a;
        if (uL.z < 0.5) { float warm = (c.r - 0.5 * (c.g + c.b)) / max(dot(c, vec3(0.333)), 1e-3); a = smoothstep(0.25, 0.9, warm); }
        else a = smoothstep(0.7, 0.92, g);
        col = mix(col, vec3(0.95, 0.07, 0.05) * (0.35 + 1.1 * g), a * step(0.02, g));
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
