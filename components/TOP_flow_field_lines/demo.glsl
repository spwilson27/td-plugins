uniform vec4 uT; // time, aspect, 0, 0
out vec4 fragColor;
vec3 hue(float h){ return clamp(abs(mod(h*6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }
void main(){
    vec2 uv = vUV.st;
    vec2 p = (uv - 0.5) * vec2(uT.y, 1.);
    vec3 col = mix(vec3(0.03, 0.04, 0.10), vec3(0.12, 0.06, 0.10), uv.y);
    for(int i = 0; i < 6; i++){
        float fi = float(i);
        vec2 c = vec2(sin(uT.x*0.21 + fi*1.9)*0.62, cos(uT.x*0.17 + fi*2.7)*0.30);
        float r = 0.10 + 0.03*fi;
        float d = length(p - c);
        vec3 h = hue(fract(fi*0.17 + 0.05*uT.x*0.2));
        col += h * smoothstep(r, r*0.15, d) * 0.9;
        col += h * exp(-pow((d - r*1.7)*22., 2.)) * 0.7;
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.));
}
