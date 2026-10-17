// SDF_from_POP / points: smooth union of spheres (|p - P_i| - r_i), looked up through the GPU grid.
// buffers: T_@ID@_p = pts (x y z r  cr cg cb 0), T_@ID@_g = cell (count, point indices), T_@ID@_b = bounds (min xyz, max xyz, delta)
// P_@ID@_0 = (grid res G, cell capacity K, blend k, 0)
// Smooth union of the spheres in reach: with m = the smallest distance and S = sum of (1 - (d_i - m) / k)^2 over the spheres
// within k of it, f = m - (k / 4) * g(S - 1), g(x) = x / (1 + x / 4). For two spheres that is exactly the polynomial smooth
// min; unlike chaining it, it does not depend on the order of the spheres, and it saturates at k below the nearest sphere.
vec4 sdf_@ID@(vec3 p){
    vec3 bmin = vec3(TDBuffer_T_@ID@_b(0, 0), TDBuffer_T_@ID@_b(0, 1), TDBuffer_T_@ID@_b(0, 2));
    vec3 bmax = vec3(TDBuffer_T_@ID@_b(0, 3), TDBuffer_T_@ID@_b(0, 4), TDBuffer_T_@ID@_b(0, 5));
    vec3 sz = bmax - bmin;
    if (!(sz.x > 0.0 && sz.y > 0.0 && sz.z > 0.0)) return vec4(1e3, 0.8, 0.8, 0.8);   // no points
    float G = P_@ID@_0.x, k = max(P_@ID@_0.z, 1e-5);
    vec3 u = (p - bmin) / sz, q = clamp(u, 0.0, 1.0);
    if (any(lessThan(u, vec3(0.0))) || any(greaterThan(u, vec3(1.0))))     // outside the grid: distance to its box
        return vec4(length((u - q) * sz) + 0.9 * TDBuffer_T_@ID@_b(0, 6), 0.8, 0.8, 0.8);   // (+ the margin the surface keeps from it)
    int Gi = int(G);
    ivec3 ci = min(ivec3(q * G), ivec3(Gi - 1));
    int c = ci.x + Gi * (ci.y + Gi * ci.z);
    int n = min(int(TDBuffer_T_@ID@_g(c, 0)), int(P_@ID@_0.y));
    float far = 0.5 * max(sz.x, max(sz.y, sz.z)) / G;     // nothing outside this cell's lists is closer than this
    float m = 1e9;
    for (int i = 0; i < n; i++){
        int j = int(TDBuffer_T_@ID@_g(c, 1 + i));
        vec3 s = vec3(TDBuffer_T_@ID@_p(j, 0), TDBuffer_T_@ID@_p(j, 1), TDBuffer_T_@ID@_p(j, 2));
        m = min(m, length(p - s) - TDBuffer_T_@ID@_p(j, 3));
    }
    if (n == 0) return vec4(far, 0.8, 0.8, 0.8);
    float S = 0.0, wsum = 0.0;
    vec3 col = vec3(0.0);
    for (int i = 0; i < n; i++){
        int j = int(TDBuffer_T_@ID@_g(c, 1 + i));
        vec3 s = vec3(TDBuffer_T_@ID@_p(j, 0), TDBuffer_T_@ID@_p(j, 1), TDBuffer_T_@ID@_p(j, 2));
        float t = (length(p - s) - TDBuffer_T_@ID@_p(j, 3) - m) / k;
        if (t >= 1.0) continue;
        float w = (1.0 - t) * (1.0 - t);
        S += w; wsum += w;
        col += w * vec3(TDBuffer_T_@ID@_p(j, 4), TDBuffer_T_@ID@_p(j, 5), TDBuffer_T_@ID@_p(j, 6));
    }
    float x = max(S - 1.0, 0.0);
    float f = m - 0.25 * k * x / (1.0 + 0.25 * x);
    return vec4(min(f, far), col / max(wsum, 1e-6));
}
