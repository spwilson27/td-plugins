// SDF_from_POP / mesh: voxelize triangles into a narrow-band distance grid plus ray-parity columns.
// in0 = the voxel columns (G^2 points; column = y * G + x), in1 = the triangles as unique points (3 per triangle).
// Threads = the points of in1 (every 3rd one handles its triangle). Three passes:
//   0  bounds reduction (atomic min/max of the vertices)        1  finalize bnd (auto: padded cube; manual: given box)
//   2  scatter: distance to the triangle for every voxel within the band -> dist[column][z] (atomic min, stored as
//      ~floatbits so that 0 = unset); ray parity along +z -> par[column] bit z (atomic xor at the first voxel above a hit)
// Output attributes (on the columns): dist uint[G], par uint[8], bnd float[6] (point 0), red uint[8] (scratch).
// uA = (G, band voxels, 0 auto / 1 manual bounds, padding fraction), uB = manual min xyz, uC = manual max xyz
uint fenc(float f){ uint u = floatBitsToUint(f); return ((u & 0x80000000u) != 0u) ? ~u : (u | 0x80000000u); }
float fdec(uint u){ return uintBitsToFloat(((u & 0x80000000u) != 0u) ? (u & 0x7fffffffu) : ~u); }
float dot2(vec3 v){ return dot(v, v); }
float udTriangle(vec3 p, vec3 a, vec3 b, vec3 c){
    vec3 ba = b - a, pa = p - a, cb = c - b, pb = p - b, ac = a - c, pc = p - c, nor = cross(ba, ac);
    float n2 = max(dot2(nor), 1e-30);
    if (sign(dot(cross(ba, nor), pa)) + sign(dot(cross(cb, nor), pb)) + sign(dot(cross(ac, nor), pc)) < 2.0)
        return sqrt(min(min(dot2(ba * clamp(dot(ba, pa) / max(dot2(ba), 1e-30), 0.0, 1.0) - pa),
                            dot2(cb * clamp(dot(cb, pb) / max(dot2(cb), 1e-30), 0.0, 1.0) - pb)),
                            dot2(ac * clamp(dot(ac, pc) / max(dot2(ac), 1e-30), 0.0, 1.0) - pc)));
    return sqrt(dot(nor, pa) * dot(nor, pa) / n2);
}

void main(){
    const uint id = TDIndex();
    if (id >= TDNumElements()) return;
    uint pass = TDPassIndex();
    int G = int(uA.x);
    if (pass == 0u){
        vec3 v = TDIn_P(1, id);
        for (int a = 0; a < 3; a++){
            atomicMax(red[0][a], ~fenc(v[a]));
            atomicMax(red[0][3 + a], fenc(v[a]));
        }
        atomicMax(red[0][6], 1u);
        return;
    }
    if (pass == 1u){
        if (id != 0u) return;
        if (uA.z > 0.5){
            for (int a = 0; a < 3; a++){ bnd[0][a] = uB[a]; bnd[0][3 + a] = uC[a]; }
        } else if (red[0][6] == 0u){
            for (int k = 0; k < 6; k++) bnd[0][k] = 0.0;
        } else {
            vec3 mn = vec3(fdec(~red[0][0]), fdec(~red[0][1]), fdec(~red[0][2]));
            vec3 mx = vec3(fdec(red[0][3]), fdec(red[0][4]), fdec(red[0][5]));
            vec3 c = 0.5 * (mn + mx);
            float h = 0.5 * max(mx.x - mn.x, max(mx.y - mn.y, mx.z - mn.z)) * (1.0 + 2.0 * uA.w) + 1e-5;
            for (int a = 0; a < 3; a++){ bnd[0][a] = c[a] - h; bnd[0][3 + a] = c[a] + h; }
        }
        return;
    }
    if (id % 3u != 0u || id + 2u >= TDNumElements()) return;
    vec3 a = TDIn_P(1, id), b = TDIn_P(1, id + 1u), c = TDIn_P(1, id + 2u);
    vec3 bmin = vec3(bnd[0][0], bnd[0][1], bnd[0][2]);
    vec3 bmax = vec3(bnd[0][3], bnd[0][4], bnd[0][5]);
    vec3 vs = max(bmax - bmin, vec3(1e-6)) / float(G);
    float bw = uA.y * min(vs.x, min(vs.y, vs.z));
    ivec3 gmax = ivec3(G - 1);
    // distance band
    vec3 tmn = min(a, min(b, c)) - bw, tmx = max(a, max(b, c)) + bw;
    ivec3 lo = clamp(ivec3(floor((tmn - bmin) / vs - 0.5)), ivec3(0), gmax);
    ivec3 hi = clamp(ivec3(ceil((tmx - bmin) / vs - 0.5)), ivec3(0), gmax);
    for (int z = lo.z; z <= hi.z; z++)
    for (int y = lo.y; y <= hi.y; y++)
    for (int x = lo.x; x <= hi.x; x++){
        float d = udTriangle(bmin + (vec3(x, y, z) + 0.5) * vs, a, b, c);
        if (d < bw) atomicMax(dist[y * G + x][z], ~floatBitsToUint(d));
    }
    // ray parity along +z (columns through the triangle's xy footprint; sample point nudged off the grid lines)
    float area = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
    if (abs(area) < 1e-14) return;
    vec2 xmn = min(a.xy, min(b.xy, c.xy)), xmx = max(a.xy, max(b.xy, c.xy));
    ivec2 cl = clamp(ivec2(floor((xmn - bmin.xy) / vs.xy - 0.5)), ivec2(0), gmax.xy);
    ivec2 ch = clamp(ivec2(ceil((xmx - bmin.xy) / vs.xy - 0.5)), ivec2(0), gmax.xy);
    for (int y = cl.y; y <= ch.y; y++)
    for (int x = cl.x; x <= ch.x; x++){
        vec2 q = bmin.xy + (vec2(x, y) + vec2(0.5003, 0.5007)) * vs.xy;
        float w0 = ((b.x - q.x) * (c.y - q.y) - (b.y - q.y) * (c.x - q.x)) / area;
        float w1 = ((c.x - q.x) * (a.y - q.y) - (c.y - q.y) * (a.x - q.x)) / area;
        float w2 = 1.0 - w0 - w1;
        if (w0 < 0.0 || w1 < 0.0 || w2 < 0.0) continue;
        float zh = w0 * a.z + w1 * b.z + w2 * c.z;
        int k0 = max(int(floor((zh - bmin.z) / vs.z + 0.5)), 0);
        if (k0 >= G) continue;
        atomicXor(par[y * G + x][k0 >> 5], 1u << uint(k0 & 31));
    }
}
