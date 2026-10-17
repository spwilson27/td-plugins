out vec4 fragColor;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec4 s = texelFetch(sTD2DInputs[0], ip, 0);
    float asp = uC.z;
    vec2 seed = vec2(ip) + uC.w*0.137;
    bool fresh = s.w < 0.5;
    bool out_ = s.x < 0. || s.x > 1. || s.y < 0. || s.y > 1.;
    if(fresh || s.z >= 1.0 || out_){
        vec2 np = vec2(hash12(seed), hash12(seed + 19.7));
        float age = fresh ? hash12(seed + 3.3)*0.98 : 0.;
        fragColor = vec4(np, age, 1.);
        return;
    }
    if(uC.x < 0.5){ fragColor = s; return; }
    vec2 d = flowDir(s.xy);
    s.xy += d * uA.z * vec2(1./asp, 1.);
    s.z += 1./max(uC.y, 1.);
    fragColor = s;
}
