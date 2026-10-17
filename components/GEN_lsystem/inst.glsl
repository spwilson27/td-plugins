// Instance data per segment. uA: mode, growth, linewidth, taper.  uB: root color, uC: tip color
uniform vec4 uA;
uniform vec4 uB;
uniform vec4 uC;
uniform vec4 uD; // look, accent
out vec4 fragColor;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec4 a = texelFetch(sTD2DInputs[0], ip, 0);  // x0 y0 x1 y1
    vec4 b = texelFetch(sTD2DInputs[1], ip, 0);  // k0 k1 depth
    vec2 d = a.zw - a.xy;
    float len = length(d);
    float g = clamp((uA.y - b.x) / max(b.y - b.x, 1e-6), 0., 1.);   // growth of this segment
    float vis = (uA.y >= b.x && len > 0.) ? 1. : 0.;
    float th = uA.z * pow(uA.w, b.z);
    int mode = int(uA.x + 0.5);
    vec4 o;
    if(mode == 0){
        vec2 m = a.xy + d * g * 0.5;
        o = vec4(m, 0., 1.);
    } else if(mode == 1){
        o = vec4(0., 0., degrees(atan(d.y, d.x)), 1.);
    } else if(mode == 2){
        float L = (len * g + th * 0.7) * vis;
        o = vec4(L, th * vis, 1., 1.);
    } else {
        float tip = (g < 1.0 && g > 0.) ? 1. : 0.;
        vec3 col = mix(uB.rgb, uC.rgb, clamp(b.y, 0., 1.));
        col = mix(col, vec3(1.), tip * 0.5);
        if(uD.x > 0.5) col = mix(mix(uB.rgb, uC.rgb, clamp(b.y, 0., 1.)), vec3(0.95,0.04,0.04), uD.y * (tip + 0.8*smoothstep(0.85,1.0,b.y)));
        o = vec4(col, 1.);
    }
    fragColor = o;
}
