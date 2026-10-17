// gather depth of field with disc / polygon bokeh. in0 color, in1 depth(r)
uniform vec4 uA; // focus, range, falloff, maxBlurPx
uniform vec4 uB; // samples, bokehBoost, blades, bladeRot
uniform vec4 uC; // resScale, 0,0,0
out vec4 fragColor;
const float GA = 2.39996323;
float cocOf(float d){
    float x = (abs(d - uA.x) - uA.y) / max(uA.z, 1e-3);
    return smoothstep(0.0, 1.0, x) * uA.w * uC.x;
}
void main(){
    vec2 uv = vUV.st;
    vec2 px = 1.0 / uTDOutputInfo.res.zw;
    vec4 c0 = texture(sTD2DInputs[0], uv);
    float coc0 = cocOf(texture(sTD2DInputs[1], uv).r);
    int N = int(uB.x);
    vec3 acc = c0.rgb * (1.0 + uB.y * pow(dot(c0.rgb, vec3(0.333)), 3.0));
    float wsum = 1.0 + uB.y * pow(dot(c0.rgb, vec3(0.333)), 3.0);
    float maxR = uA.w * uC.x;
    int blades = int(uB.z + 0.5);
    for(int i = 0; i < 160; i++){
        if(i >= N) break;
        float fi = float(i) + 0.5;
        float r = sqrt(fi / float(N));
        float a = fi * GA;
        float shape = 1.0;
        if(blades >= 3){
            float sec = 6.2831853 / float(blades);
            float aa = mod(a + uB.w, sec) - sec * 0.5;
            shape = cos(sec * 0.5) / cos(aa);
        }
        vec2 o = vec2(cos(a), sin(a)) * r * shape * maxR;
        float dist = length(o);
        vec2 suv = uv + o * px;
        vec3 sc = texture(sTD2DInputs[0], suv).rgb;
        float cocS = cocOf(texture(sTD2DInputs[1], suv).r);
        // sample contributes if its own blur disc reaches us; blurred centre pixels gather from in-focus neighbours too
        float reach = smoothstep(dist - 1.0, dist + 1.0, max(cocS, 0.0));
        float inner = smoothstep(dist - 1.0, dist + 1.0, coc0);
        float w = reach * inner * (1.0 + uB.y * pow(dot(sc, vec3(0.333)), 3.0));
        acc += sc * w; wsum += w;
    }
    fragColor = TDOutputSwizzle(vec4(acc / wsum, c0.a));
}
