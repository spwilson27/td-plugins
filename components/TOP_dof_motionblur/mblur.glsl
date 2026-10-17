// velocity motion blur. in0 color, in1 velocity (r,g in uv-ish units, pixels*scale). uA: amount(px scale), samples, hasVel, 0
uniform vec4 uA;
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec4 c = texture(sTD2DInputs[0], uv);
    if(uA.z < 0.5 || uA.x <= 0.0){ fragColor = TDOutputSwizzle(c); return; }
    vec2 v = texture(sTD2DInputs[1], uv).rg * uA.x;
    int N = int(uA.y);
    vec3 acc = c.rgb; float w = 1.0;
    for(int i = 1; i < 64; i++){
        if(i >= N) break;
        float t = float(i) / float(N - 1) - 0.5;
        vec3 s = texture(sTD2DInputs[0], uv + v * t).rgb;
        acc += s; w += 1.0;
    }
    fragColor = TDOutputSwizzle(vec4(acc / w, c.a));
}
