// Rest positions + pin flag. rgb = rest position, a = pinned (1) / free (0)
uniform vec4 uR;   // x=N y=cloth size z=pin mode (0 top row, 1 corners, 2 none) w=top y
out vec4 fragColor;
void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    int N = int(uR.x + 0.5);
    vec2 g = vec2(ip) / float(N - 1);
    vec3 p = vec3((g.x - 0.5) * uR.y, uR.w - (1.0 - g.y) * uR.y, 0.0);
    int mode = int(uR.z + 0.5);
    float pin = 0.0;
    bool top = ip.y == N - 1;
    if (mode == 0) pin = top ? 1.0 : 0.0;
    else if (mode == 1) pin = (top && (ip.x == 0 || ip.x == N - 1)) ? 1.0 : 0.0;
    fragColor = vec4(p, pin);
}
