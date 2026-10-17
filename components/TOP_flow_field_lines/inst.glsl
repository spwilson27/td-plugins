uniform vec4 uA; // step, speedByMag, aspect, trail (segment length in steps)
uniform vec4 uB; // thickness(world), colorMode(0 image,1 direction,2 age,3 line), saturation, mode(0 pos,1 rot,2 scale,3 color)
uniform vec4 uC; // line colour rgb, 0
out vec4 fragColor;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec4 s = texelFetch(sTD2DInputs[0], ip, 0);
    float asp = uA.z;
    vec3 f = fieldAt(sTD2DInputs[1], s.xy);
    float sp = mix(1., max(f.z, 0.15), uA.y);
    vec2 p1 = s.xy;
    vec2 p0 = p1 - f.xy * uA.x * sp * uA.w * vec2(1./asp, 1.);
    vec2 w0 = (p0 - 0.5) * vec2(asp, 1.), w1 = (p1 - 0.5) * vec2(asp, 1.);
    vec2 dl = w1 - w0;
    float len = length(dl);
    float vis = (s.w > 0.5 && s.z < 1.0) ? 1. : 0.;
    float th = uB.x;
    int mode = int(uB.w + 0.5);
    vec4 o;
    if(mode == 0) o = vec4(0.5*(w0+w1), 0., 1.);
    else if(mode == 1) o = vec4(0., 0., degrees(atan(dl.y, dl.x)), 1.);
    else if(mode == 2) o = vec4((len + th)*vis, th*vis, 1., 1.);
    else {
        float fade = smoothstep(0., 0.12, s.z) * smoothstep(1.0, 0.8, s.z);
        int cm = int(uB.y + 0.5);
        vec3 col;
        if(cm == 0){
            col = texture(sTD2DInputs[2], clamp(p1, 0., 1.)).rgb;
            float l = dot(col, vec3(0.299, 0.587, 0.114));
            col = max(mix(vec3(l), col, uB.z), 0.);
        }
        else if(cm == 1) col = palette(atan(f.y, f.x)/6.28318 + 0.5);
        else if(cm == 2) col = palette(s.z);
        else col = uC.rgb;
        o = vec4(col * fade, 1.);
    }
    fragColor = o;
}
