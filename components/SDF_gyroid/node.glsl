vec4 sdf_@ID@(vec3 p){
    vec4 a = P_@ID@_0;
    vec3 q = p * a.x;
    int t = int(a.z + 0.5);
    float g;
    if (t == 0) g = dot(sin(q), cos(q.zxy));
    else if (t == 1) g = (cos(q.x) + cos(q.y) + cos(q.z)) * 0.5;
    else g = sin(q.x) * sin(q.y) * sin(q.z) + sin(q.x) * cos(q.y) * cos(q.z) + cos(q.x) * sin(q.y) * cos(q.z) + cos(q.x) * cos(q.y) * sin(q.z);
    float d = (abs(g) - a.y) / (a.x * 1.6);
    if (a.w > 0.0) d = max(d, length(p) - a.w);
    return vec4(d, mix(P_@ID@_1.xyz, P_@ID@_2.xyz, clamp(0.5 + 0.5 * g, 0.0, 1.0)));
}
