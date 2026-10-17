// bake the SDF scene into a 3D texture: R = signed distance (world units), GBA = albedo
// (compute shader: a 3D pixel shader only binds POP buffers / textures of the scene on some slices)
//@@SDF@@
uniform vec4 uBc;   // bounds center xyz, resolution (voxels per side)
uniform vec4 uBs;   // bounds size xyz
layout (local_size_x = 8, local_size_y = 8, local_size_z = 4) in;
void main(){
    ivec3 v = ivec3(gl_GlobalInvocationID);
    if (any(greaterThanEqual(v, ivec3(int(uBc.w))))) return;
    vec3 p = uBc.xyz + ((vec3(v) + 0.5) / uBc.w - 0.5) * uBs.xyz;
    TDImageStoreOutput(0, gl_GlobalInvocationID, sdScene(p));
}
