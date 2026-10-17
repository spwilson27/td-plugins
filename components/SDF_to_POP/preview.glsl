// SDF node preview: small orbiting raymarch of the node's own SDF
//@@SDF@@
//@@LIB@@
uniform vec4 uPv;   // x = time
out vec4 fragColor;
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    vec2 uv = (vUV.st * 2.0 - 1.0) * vec2(res.x / res.y, 1.0);
    float a = uPv.x * 0.45;
    vec3 ro = vec3(sin(a) * 3.0, 1.5, cos(a) * 3.0);
    vec3 fw = normalize(-ro), rt = normalize(cross(fw, vec3(0, 1, 0))), up = cross(rt, fw);
    vec3 rd = normalize(fw * 1.6 + rt * uv.x + up * uv.y);
    vec3 sky = sdSky(rd);
    vec3 col = sky * 0.7;
    float t; vec3 alb;
    if (sdMarch(ro, rd, 0.1, 14.0, 72, 0.002, 0.9, t, alb)){
        vec3 p = ro + rd * t;
        vec3 n = sdNormal(p, 0.002);
        col = sdLight(p, n, rd, alb, normalize(vec3(0.6, 0.8, 0.5)), 8.0, 1.0, sky);
        col = mix(col, sky * 0.7, 1.0 - exp(-0.004 * t * t));
    }
    col = pow(col, vec3(0.4545));
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
