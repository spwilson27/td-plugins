// Per-instance data texture (one pixel per instance). uA.w selects the output channel set:
// 0 = translate, 1 = rotate (deg), 2 = scale, 3 = color
uniform vec4 uA; // countx, county, spacing, mode
uniform vec4 uB; // heightamt, scaleamt, rotamt, basesize
uniform vec4 uC; // invert, colormix, heightbase, -
uniform vec4 uD; // look, accent
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    float L = dot(c, vec3(0.2126, 0.7152, 0.0722));
    if(uC.x > 0.5) L = 1.0 - L;
    L = clamp(L, 0., 1.);
    float sy = max(0.02, uC.z + uB.x * L);
    float s  = uB.w * mix(1.0, 0.15 + 1.1*L, uB.y);
    int mode = int(uA.w + 0.5);
    vec4 o = vec4(0.);
    if(mode == 0){
        vec2 ij = floor(uv * uA.xy);
        vec2 p = (ij - (uA.xy - 1.0) * 0.5) * uA.z;
        o = vec4(p.x, sy * 0.5, p.y, 1.);
    } else if(mode == 1){
        o = vec4(0., uB.z * L * 360.0, 0., 1.);
    } else if(mode == 2){
        o = vec4(s, sy, s, 1.);
    } else {
        o = vec4(mix(vec3(1.), c, uC.y), 1.);
        if(uD.x > 0.5){
            vec3 m = vec3(0.12 + 0.88*L) * vec3(0.95,0.93,0.88);
            m = mix(m, vec3(0.95,0.04,0.04), uD.y*smoothstep(0.78,0.92,L));
            o = vec4(m, 1.);
        }
    }
    fragColor = o;
}
