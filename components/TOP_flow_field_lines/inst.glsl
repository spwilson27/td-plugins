out vec4 fragColor;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec4 s = texelFetch(sTD2DInputs[0], ip, 0);
    float asp = uC.z;
    vec2 d = flowDir(s.xy);
    vec2 p1 = s.xy;
    vec2 p0 = p1 - d * uA.z * uB.x * vec2(1./asp, 1.);
    vec2 w0 = (p0 - 0.5) * vec2(asp, 1.), w1 = (p1 - 0.5) * vec2(asp, 1.);
    vec2 dl = w1 - w0;
    float len = length(dl);
    float vis = (s.w > 0.5 && s.z < 1.0) ? 1. : 0.;
    float th = uD.x;
    int mode = int(uE.x + 0.5);
    vec4 o;
    if(mode == 0) o = vec4(0.5*(w0+w1), 0., 1.);
    else if(mode == 1) o = vec4(0., 0., degrees(atan(dl.y, dl.x)), 1.);
    else if(mode == 2) o = vec4((len + th)*vis, th*vis, 1., 1.);
    else {
        float fade = smoothstep(0., 0.12, s.z) * smoothstep(1.0, 0.8, s.z);
        vec3 col;
        int cm = uF.x > 0.5 ? 0 : int(uD.z + 0.5);
        if(cm == 0) col = vec3(uE.y, uE.z, uE.w);
        else if(cm == 1) col = palette(atan(d.y, d.x)/6.28318 + 0.5);
        else if(cm == 2) col = palette(s.z);
        else col = palette(hash12(vec2(ip)));
        if(uF.x > 0.5){
            col = vec3(0.93,0.91,0.86)*0.55;
            if(hash12(vec2(ip) + 7.7) < uF.y*0.15) col = vec3(1.0,0.04,0.04)*1.1;
        }
        o = vec4(col * fade * uD.y, 1.);
    }
    fragColor = o;
}
