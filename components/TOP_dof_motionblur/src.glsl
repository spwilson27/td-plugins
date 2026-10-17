// default scene: perspective floor lines + bokeh dots at different depths. uA.x = p (loop phase), uA.y = output (0 color, 1 depth)
uniform vec4 uA;
out vec4 fragColor;
const float TAU = 6.28318530718;
float h11(float n){ return fract(sin(n*127.1)*43758.5453); }
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = vUV.st;
    vec2 q = (uv - 0.5) * vec2(res.x/res.y, 1.0);
    float p = uA.x;
    vec3 col = vec3(0.01); float depth = 1.0;
    // floor: horizon at y = 0.08, depth 1 far -> 0 near (bottom)
    float hy = q.y - 0.08;
    if(hy < 0.0){
        float z = 0.5 / max(-hy, 0.002);
        float d = clamp(1.0 - (-hy) / 0.58, 0.0, 1.0);
        float zz = z * 1.2 - p * 6.0;
        float line = smoothstep(-0.02, 0.03, abs(fract(zz) - 0.5) - 0.45);
        float vx = abs(fract(q.x * z * 0.5) - 0.5);
        float vline = smoothstep(-0.01, 0.02, vx - 0.47);
        col += vec3(0.8,0.8,0.78) * (line + vline) * 0.8 * exp(-z * 0.12);
        depth = d;
    }
    // dots (nearest wins)
    for(int i = 0; i < 70; i++){
        float fi = float(i);
        float dz = h11(fi * 3.7 + 1.0);
        vec2 base = (vec2(h11(fi*1.3+0.1), h11(fi*2.9+0.7)) - 0.5) * vec2(1.9, 0.9);
        float k = 1.0 + floor(h11(fi + 9.0) * 3.0);
        vec2 pos = base + 0.06 * vec2(sin(TAU*(p*k) + fi), cos(TAU*(p*k) + fi*1.7));
        float rad = 0.006 + 0.02 * h11(fi * 5.1 + 2.0);
        float dd = length(q - pos);
        if(dd < rad && dz < depth){
            depth = dz;
            float hot = step(0.88, h11(fi * 8.3));
            vec3 c = mix(vec3(0.95, 0.94, 0.9), vec3(1.0, 0.1, 0.05), hot);
            col = c * (0.7 + 0.9 * h11(fi * 4.4));
        }
    }
    if(uA.y > 0.5) fragColor = TDOutputSwizzle(vec4(vec3(depth), 1.0));
    else fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
