// bake the SDF scene into a 3D texture: R = signed distance (world units), GBA = albedo
//@@SDF@@
uniform vec4 uBc;   // bounds center xyz
uniform vec4 uBs;   // bounds size xyz
out vec4 fragColor;
void main(){
    vec3 uvw = vUV.xyz;
    vec3 p = uBc.xyz + (uvw - 0.5) * uBs.xyz;
    vec4 s = sdScene(p);
    fragColor = TDOutputSwizzle(s);
}
