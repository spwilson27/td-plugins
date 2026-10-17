uniform sampler2D uPos;
uniform float uN;
out vec3 vNrm;
out vec3 vWorld;
out vec2 vG;
vec3 fetchP(ivec2 i){ int n = int(uN + 0.5); i = clamp(i, ivec2(0), ivec2(n - 1)); return texelFetch(uPos, i, 0).xyz; }
void main(){
    vec2 g = uv[0].st;
    ivec2 i = ivec2(floor(g * (uN - 1.0) + 0.5));
    vec3 p = fetchP(i);
    vec3 dx = fetchP(i + ivec2(1, 0)) - fetchP(i - ivec2(1, 0));
    vec3 dy = fetchP(i + ivec2(0, 1)) - fetchP(i - ivec2(0, 1));
    vNrm = normalize(cross(dx, dy) + vec3(1e-9));
    vWorld = p;
    vG = g;
    gl_Position = TDWorldToProj(vec4(p, 1.0));
}
