// input 0 = state (grid res), input 1 = source image
uniform vec4 uCol0; uniform vec4 uCol1; uniform vec4 uCol2; uniform vec4 uCol3; // dead, alive(young), old, aux
uniform vec4 uM;   // x=rule y=colour mode (0 input,1 age,2 flat) z=age range w=ghost amount
uniform vec4 uN;   // x=backdrop (input visible behind) y=cell gap z=mix w=vivid
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec2 g = vec2(textureSize(sTD2DInputs[0], 0));
    vec2 cp = uv * g;
    ivec2 ic = ivec2(clamp(floor(cp), vec2(0.0), g - 1.0));
    vec4 c = texelFetch(sTD2DInputs[0], ic, 0);
    vec3 dry = texture(sTD2DInputs[1], uv).rgb;
    vec3 cell = texture(sTD2DInputs[1], (vec2(ic) + 0.5) / g).rgb;
    float mx = max(cell.r, max(cell.g, cell.b));
    vec3 base = mix(cell, cell / max(mx, 0.3), uN.w);

    int rule = int(uM.x + 0.5);
    int mode = int(uM.y + 0.5);
    float s = c.r;
    float t = clamp(c.g / max(uM.z, 1.0), 0.0, 1.0);

    // live-cell colour
    vec3 live = vec3(0.0);
    bool alive = s > 0.5;
    if (mode == 0) {                                   // cells keep the input's colours
        if (rule == 1) live = s > 1.5 ? mix(base * 0.6, uCol3.rgb, 0.5) : base;
        else if (rule == 2) live = s > 2.5 ? base * 0.55 : (s > 1.5 ? mix(base, uCol2.rgb, 0.6) : mix(base, vec3(1.0), 0.7));
        else live = mix(base, vec3(1.0), 0.45 * (1.0 - clamp(c.g / 3.0, 0.0, 1.0)));   // newborn cells flash
    } else {
        vec3 a = mode == 1 ? mix(uCol1.rgb, uCol2.rgb, t) : uCol1.rgb;
        if (rule == 1) live = s > 1.5 ? uCol3.rgb : a;
        else if (rule == 2) live = s > 2.5 ? uCol3.rgb : (s > 1.5 ? uCol2.rgb : uCol1.rgb);
        else live = a;
    }
    // dead-cell colour: input shows through (Backdrop) plus a fading trail
    vec3 trailc = mode == 0 ? base : uCol2.rgb;
    vec3 dead = mode == 0 ? dry * uN.x : mix(uCol0.rgb, dry, uN.x);
    dead += trailc * c.b * uM.w * (mode == 0 ? 0.8 : 0.5) * (alive ? 0.0 : 1.0);
    // optional gap between cells
    float body = 1.0;
    if (uN.y > 0.0) {
        vec2 f = abs(fract(cp) - 0.5) * 2.0;
        float e = max(f.x, f.y);
        body = 1.0 - smoothstep(1.0 - uN.y - 0.15, 1.0 - uN.y, e);
    }
    vec3 res = alive ? mix(dead, live, body) : dead;
    res = mix(dry, res, uN.z);
    fragColor = TDOutputSwizzle(vec4(res, 1.0));
}
