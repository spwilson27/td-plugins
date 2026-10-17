// depth preparation. in0 = color, in1 = depth source. uA: mode (0 auto,1 depth in,2 luminance,3 radial), hasIn1, hasIn2, invert
uniform vec4 uA;
out vec4 fragColor;
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = vUV.st;
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    float d = texture(sTD2DInputs[1], uv).r;
    float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
    vec2 q = (uv - 0.5) * vec2(res.x/res.y, 1.0);
    float rad = clamp(length(q) * 1.15, 0.0, 1.0);
    int mode = int(uA.x + 0.5);
    float o;
    if(mode == 0) o = (uA.z > 0.5 || uA.y < 0.5) ? d : rad;
    else if(mode == 1) o = d;
    else if(mode == 2) o = clamp(lum, 0.0, 1.0);
    else o = rad;
    if(uA.w > 0.5) o = 1.0 - o;
    fragColor = TDOutputSwizzle(vec4(vec3(o), 1.0));
}
