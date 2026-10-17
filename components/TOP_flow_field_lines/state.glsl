uniform vec4 uA; // step(height fraction), speedByMag, aspect, frame
uniform vec4 uB; // play, lifetime(frames), 0, 0
out vec4 fragColor;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec4 s = texelFetch(sTD2DInputs[0], ip, 0);
    float asp = uA.z;
    vec2 seed = vec2(ip) + uA.w*0.137;
    bool fresh = s.w < 0.5;
    bool out_ = s.x < 0. || s.x > 1. || s.y < 0. || s.y > 1.;
    if(fresh || s.z >= 1.0 || out_){
        vec2 np = vec2(hash12(seed), hash12(seed + 19.7));
        float age = fresh ? hash12(seed + 3.3)*0.98 : 0.;
        fragColor = vec4(np, age, 1.);
        return;
    }
    if(uB.x < 0.5){ fragColor = s; return; }
    vec3 f = fieldAt(sTD2DInputs[1], s.xy);
    float sp = mix(1., max(f.z, 0.15), uA.y);
    s.xy += f.xy * uA.x * sp * vec2(1./asp, 1.);
    s.z += 1./max(uB.y, 1.);
    fragColor = s;
}
