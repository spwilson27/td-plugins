vec4 sdf_@ID@(vec3 p){
    vec3 n = P_@ID@_0.xyz;
    float d = dot(p, n) - P_@ID@_0.w;
    vec3 col = P_@ID@_1.xyz;
    if (P_@ID@_2.x > 0.0){
        vec3 an = abs(n);
        vec2 uv = an.y >= an.x && an.y >= an.z ? p.xz : (an.x >= an.z ? p.yz : p.xy);
        vec2 c = floor(uv / P_@ID@_2.x);
        float chk = mod(c.x + c.y, 2.0);
        float fade = exp(-0.02 * dot(uv, uv));
        col = mix(col, P_@ID@_3.xyz, chk * fade);
    }
    return vec4(d, col);
}
