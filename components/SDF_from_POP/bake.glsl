// SDF_from_POP / mesh: the voxel columns (vox.glsl) -> 3D texture (compute: a 3D pixel shader only binds POP buffers on some slices).
// R = signed distance / band width (so -1..1, precise in fp16), GBA = colour.
// Sign = ray parity (odd number of surface crossings below the voxel = inside); voxels outside the narrow band get +-band.
// buffers: vdist = dist, vpar = par, vbnd = bnd.   uA = (G, band voxels, 0, 0), uCol = colour
uniform vec4 uA;
uniform vec4 uCol;
layout (local_size_x = 8, local_size_y = 8, local_size_z = 4) in;
void main(){
    int G = int(uA.x);
    ivec3 v = ivec3(gl_GlobalInvocationID);
    if (any(greaterThanEqual(v, ivec3(G)))) return;
    int col = v.y * G + v.x;
    vec3 bmin = vec3(TDBuffer_vbnd(0, 0), TDBuffer_vbnd(0, 1), TDBuffer_vbnd(0, 2));
    vec3 bmax = vec3(TDBuffer_vbnd(0, 3), TDBuffer_vbnd(0, 4), TDBuffer_vbnd(0, 5));
    vec3 vs = max(bmax - bmin, vec3(1e-6)) / float(G);
    float bw = uA.y * min(vs.x, min(vs.y, vs.z));
    uint u = TDBuffer_vdist(col, v.z);
    float d = (u == 0u) ? bw : uintBitsToFloat(~u);
    int w = v.z >> 5;
    uint par = 0u;
    for (int i = 0; i < w; i++) par ^= bitCount(TDBuffer_vpar(col, i)) & 1u;
    int b = v.z & 31;
    uint mask = (b == 31) ? 0xFFFFFFFFu : ((1u << uint(b + 1)) - 1u);
    par ^= bitCount(TDBuffer_vpar(col, w) & mask) & 1u;
    if (par == 1u) d = -d;
    TDImageStoreOutput(0, gl_GlobalInvocationID, vec4(d / max(bw, 1e-9), uCol.rgb));
}
