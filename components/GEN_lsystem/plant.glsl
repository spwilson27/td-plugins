// Planting points -> per-tree rotation (about Y), scale, and a keep flag thinning the points to at most Maxtrees.
// uA: seed, variation, treesize, maxtrees
uniform vec4 uA;
float h11(float n){ return fract(sin(n * 127.1 + uA.x * 311.7) * 43758.5453); }
void main(){
    const uint id = TDIndex();
    if(id >= TDNumElements()) return;
    float f = float(id);
    float rot = h11(f + 1.0) * 360.0 * uA.y;
    float sc = uA.z * (1.0 + (h11(f + 7.0) - 0.5) * 0.7 * uA.y);
    TreeRot[id] = vec3(0.0, rot, 0.0);
    TreeScale[id] = vec3(sc);
    uint step = max(1u, (TDNumElements() + uint(max(uA.w, 1.0)) - 1u) / uint(max(uA.w, 1.0)));
    TreeKeep[id] = (id % step == 0u) ? 1.0 : 0.0;
}
