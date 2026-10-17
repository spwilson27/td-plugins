// Template tree (lines, 2 points per segment) -> growth + colour + line width. One thread per point.
// Per point: P = segment end position, Color = (key along path, depth, seg start key, seg end key), Tex = segment start position.
// uA: growth, linewidth, taper, beat ; uB: root colour (rgb), band1 ; uC: tip colour (rgb) ; uD: mono look, accent
uniform vec4 uA;
uniform vec4 uB;
uniform vec4 uC;
uniform vec4 uD;
void main(){
    const uint id = TDIndex();
    if(id >= TDNumElements()) return;
    vec3 pe = TDIn_P();
    vec4 c  = TDIn_Color();
    vec3 ps = TDIn_Tex();
    bool isEnd = (id & 1u) == 1u;
    float g = clamp((uA.x - c.b) / max(c.a - c.b, 1e-6), 0.0, 1.0);   // growth of this segment
    vec3 pos = isEnd ? mix(ps, pe, g) : ps;
    float tip = (g > 0.0 && g < 1.0) ? 1.0 : 0.0;
    float t = clamp(c.r, 0.0, 1.0);
    vec3 col = mix(uB.rgb, uC.rgb, t);
    col = mix(col, vec3(1.0), (tip * 0.5 + uA.w * 0.35) * (isEnd ? 1.0 : 0.0));
    if(uD.x > 0.5){
        col = mix(uB.rgb, uC.rgb, t);
        col = mix(col, vec3(0.95, 0.04, 0.04), uD.y * (tip + 0.8 * smoothstep(0.85, 1.0, t)));
    }
    P[id] = pos;
    Color[id] = vec4(col, 1.0);
    LineWidth[id] = uA.y * pow(uA.z, c.g) * (1.0 + 3.0 * uB.w) * (g > 0.0 ? 1.0 : 0.0);
}
