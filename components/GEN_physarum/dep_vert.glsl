uniform sampler2D uAgents;
uniform float uCount;
uniform float uDeposit;
uniform float uAgentsW;
uniform vec2 uPx;
flat out float vDep;
void main(){
    int id = gl_InstanceID;
    int w = int(uAgentsW);
    vec4 a = texelFetch(uAgents, ivec2(id % w, id / w), 0);
    vDep = float(id) < uCount ? uDeposit : 0.0;
    gl_Position = vec4(a.xy*2.0-1.0 + P.xy*uPx, 0.0, 1.0);
}
