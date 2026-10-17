uniform sampler2D uPos;
uniform float uCount; uniform float uW;
uniform vec4 uView;    // x=scale y=point size px z=colour speed scale w=intensity
uniform vec2 uPx;      // 2/res
uniform vec3 uC1; uniform vec3 uC2;
out vec3 vCol;
void main(){
    int id = gl_InstanceID;
    int w = int(uW);
    vec4 a = texelFetch(uPos, ivec2(id % w, id / w), 0);
    float t = clamp((a.w - 1.0) * uView.z, 0.0, 1.0);
    vCol = mix(uC1, uC2, t) * uView.w;
    vec3 wp = vec3(a.x, a.z, a.y) * uView.x;
    vec4 cp = TDWorldToProj(vec4(wp, 1.0));
    cp.xy += P.xy * uPx * uView.y * cp.w;
    if (float(id) >= uCount) cp = vec4(2.0, 2.0, 2.0, 1.0);
    gl_Position = cp;
}
