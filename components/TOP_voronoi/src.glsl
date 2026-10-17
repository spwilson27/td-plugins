// preview-only demo image: soft colourful drifting blobs (used only when in1 is not connected)
uniform vec4 uP; // time
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st; float aspect = uTDOutputInfo.res.z/uTDOutputInfo.res.w;
    vec2 p = vec2(uv.x*aspect, uv.y);
    float t = uP.x*0.15;
    vec3 col = vec3(0.04,0.06,0.12);
    for(int i=0;i<7;i++){
        float fi = float(i);
        vec2 c = vec2(aspect*(0.5+0.4*sin(t*(0.7+0.13*fi)+fi*2.1)), 0.5+0.38*cos(t*(0.6+0.11*fi)+fi*1.7));
        float r = 0.16 + 0.07*sin(fi*3.3+t);
        float w = smoothstep(r, r*0.15, distance(p, c));
        vec3 hue = 0.55+0.45*cos(6.2831*(fi*0.17+vec3(0.0,0.33,0.67)+t*0.2));
        col = mix(col, hue, w);
    }
    col += 0.06*sin(uv.x*40.+t*4.)*sin(uv.y*30.);
    fragColor = TDOutputSwizzle(vec4(col,1.));
}
