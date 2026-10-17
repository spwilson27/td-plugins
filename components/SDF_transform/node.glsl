vec4 sdf_@ID@(vec3 p){
    float s = max(P_@ID@_0.w, 1e-4);
    vec3 pp = p - P_@ID@_0.xyz;
    vec3 q = vec3(dot(P_@ID@_1.xyz, pp), dot(P_@ID@_2.xyz, pp), dot(P_@ID@_3.xyz, pp)) / s;
    vec4 r = @A@(q);
    r.x *= s;
    return r;
}
