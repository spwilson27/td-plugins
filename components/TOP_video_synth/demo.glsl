// preview-only demo picture: colourful rings, bars and a drifting disc (shows displacement and hue clearly)
uniform vec4 uT;
out vec4 fragColor;
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = (vUV.st - 0.5) * vec2(res.x / res.y, 1.0);
    float t = uT.x;
    float r = length(p);
    vec3 c = 0.5 + 0.5 * cos(vec3(0.0, 2.1, 4.2) + r * 6.0 - t * 0.5);
    c *= 0.35 + 0.65 * step(0.5, fract(p.x * 4.0 + 0.3 * sin(t * 0.3)));
    c = mix(c, vec3(0.92, 0.9, 0.8), smoothstep(0.012, 0.0, abs(fract(p.y * 5.0) - 0.5) - 0.42));
    vec2 q = p - vec2(0.35 * sin(t * 0.6), 0.2 * cos(t * 0.45));
    c = mix(c, vec3(1.0, 0.25, 0.1), smoothstep(0.17, 0.15, length(q)));
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
