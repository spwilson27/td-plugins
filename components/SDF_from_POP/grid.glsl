// SDF_from_POP / points: uniform grid over the points, built on the GPU every frame.
// in0 = the grid cells (G^3 points, only their count matters), in1 = the packed points (pack.glsl).
// Threads = the points of in1. Three passes:
//   0  bounds reduction (atomic min/max of the point positions and the largest radius)
//   1  finalize the bounds: bnd = [min xyz, max xyz, delta] grown by (largest radius + blend + delta), delta = half a cell
//   2  bin: every point is appended to each cell its sphere of influence (radius + blend + half a cell) touches
// Output attributes (on the cells): cell[c] = (count, point index 0 .. K-1) as uint[K+1] (count may exceed K: extra
// points are dropped), bnd[0] = bounds as float[7], red[0] = reduction scratch. Cell c = x + G * (y + G * z).
// uA = (G, K, blend, 0)
uint fenc(float f){ uint u = floatBitsToUint(f); return ((u & 0x80000000u) != 0u) ? ~u : (u | 0x80000000u); }
float fdec(uint u){ return uintBitsToFloat(((u & 0x80000000u) != 0u) ? (u & 0x7fffffffu) : ~u); }

void main(){
    const uint id = TDIndex();
    if (id >= TDNumElements()) return;
    uint pass = TDPassIndex();
    vec4 s = vec4(TDIn_pts(1, id, 0), TDIn_pts(1, id, 1), TDIn_pts(1, id, 2), TDIn_pts(1, id, 3));
    if (pass == 0u){
        if (s.w < 0.0) return;
        for (int a = 0; a < 3; a++){
            atomicMax(red[0][a], ~fenc(s[a]));
            atomicMax(red[0][3 + a], fenc(s[a]));
        }
        atomicMax(red[0][6], floatBitsToUint(s.w));
        return;
    }
    if (pass == 1u){
        if (id != 0u) return;
        if (red[0][6] == 0u){ for (int k = 0; k < 7; k++) bnd[0][k] = 0.0; return; }   // no valid points: empty box
        float rm = uintBitsToFloat(red[0][6]) + uA.z;
        vec3 mn = vec3(fdec(~red[0][0]), fdec(~red[0][1]), fdec(~red[0][2]));
        vec3 mx = vec3(fdec(red[0][3]), fdec(red[0][4]), fdec(red[0][5]));
        float delta = 0.5 * max(max(mx.x - mn.x, max(mx.y - mn.y, mx.z - mn.z)) + 2.0 * rm, 1e-4) / uA.x;
        for (int a = 0; a < 3; a++){
            bnd[0][a] = mn[a] - rm - delta;
            bnd[0][3 + a] = mx[a] + rm + delta;
        }
        bnd[0][6] = delta;
        return;
    }
    if (s.w < 0.0) return;
    vec3 bmin = vec3(bnd[0][0], bnd[0][1], bnd[0][2]);
    vec3 bmax = vec3(bnd[0][3], bnd[0][4], bnd[0][5]);
    int G = int(uA.x), K = int(uA.y);
    vec3 cs = max(bmax - bmin, vec3(1e-6)) / float(G);
    float infl = s.w + uA.z + 0.5 * max(cs.x, max(cs.y, cs.z));
    ivec3 lo = clamp(ivec3(floor((s.xyz - infl - bmin) / cs)), ivec3(0), ivec3(G - 1));
    ivec3 hi = clamp(ivec3(floor((s.xyz + infl - bmin) / cs)), ivec3(0), ivec3(G - 1));
    for (int z = lo.z; z <= hi.z; z++)
    for (int y = lo.y; y <= hi.y; y++)
    for (int x = lo.x; x <= hi.x; x++){
        int c = x + G * (y + G * z);
        uint slot = atomicAdd(cell[c][0], 1u);
        if (slot < uint(K)) cell[c][1 + slot] = id;
    }
}
