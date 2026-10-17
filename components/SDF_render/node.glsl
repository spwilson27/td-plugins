// SDF_render: raymarch an SDF scene -> color, linear depth, view normals, world position
//@@SDF@@
//@@LIB@@
uniform vec4 uCamPos;   // xyz position, w = tan(fov/2)
uniform vec4 uCamR;     // xyz right, w = fov mode (0 horizontal, 1 vertical)
uniform vec4 uCamU;     // xyz up
uniform vec4 uCamF;     // xyz forward
uniform vec4 uA;        // maxdist, steps, epsilon, step scale
uniform vec4 uB;        // shadow hardness, ao, fog density, reflect
uniform vec4 uC;        // key light direction xyz, gamma
uniform vec4 uD;        // fog color rgb, alpha-on-miss
uniform vec4 uE;        // background color rgb, background mode (0 environment, 1 solid)
layout(location = 0) out vec4 fragColor;
layout(location = 1) out vec4 fragDepth;
layout(location = 2) out vec4 fragNormal;
layout(location = 3) out vec4 fragPos;

vec3 envc(vec3 d){
    vec2 e = vec2(atan(d.z, d.x) / 6.2831853 + 0.5, asin(clamp(d.y, -1.0, 1.0)) / 3.14159265 + 0.5);
    return texture(sTD2DInputs[0], e).rgb;
}

void main(){
    vec2 res = uTDOutputInfo.res.zw;
    float asp = res.x / res.y;
    vec2 uv = vUV.st * 2.0 - 1.0;
    vec2 sc = uCamR.w < 0.5 ? vec2(1.0, 1.0 / asp) : vec2(asp, 1.0);
    vec3 ro = uCamPos.xyz;
    vec3 rd = normalize(uCamF.xyz + (uCamR.xyz * uv.x * sc.x + uCamU.xyz * uv.y * sc.y) * uCamPos.w);
    float tmax = uA.x, eps = uA.z;
    float t; vec3 alb;
    bool hit = sdMarch(ro, rd, 0.0, tmax, int(uA.y), eps, uA.w, t, alb);
    vec3 bg = uE.w < 0.5 ? envc(rd) : uE.rgb;
    vec3 col = bg;
    vec4 dep = vec4(tmax, tmax, tmax, 0.0), nrm = vec4(0.0), wp = vec4(0.0);
    float a = 1.0;
    if (hit){
        vec3 p = ro + rd * t;
        vec3 n = sdNormal(p, max(eps, 0.0005));
        vec3 sky = sdSky(n);
        col = sdLight(p, n, rd, alb, normalize(uC.xyz), uB.x, uB.y, sky);
        if (uB.w > 0.0){
            vec3 rc = envc(reflect(rd, n));
            float fr = pow(clamp(1.0 + dot(n, rd), 0.0, 1.0), 4.0);
            col = mix(col, rc * mix(vec3(1.0), alb, 0.35), uB.w * mix(0.55, 1.0, fr));
        }
        col = mix(col, uD.rgb, 1.0 - exp(-uB.z * t));
        float z = dot(p - ro, uCamF.xyz);
        dep = vec4(z, z, z, 1.0);
        nrm = vec4(dot(n, uCamR.xyz), dot(n, uCamU.xyz), dot(n, -uCamF.xyz), 1.0);
        wp = vec4(p, 1.0);
    } else {
        a = uD.w;
    }
    col = max(col, 0.0);
    col = clamp((col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14), 0.0, 1.0);
    col = pow(col, vec3(1.0 / uC.w));
    fragColor = TDOutputSwizzle(vec4(col, a));
    fragDepth = TDOutputSwizzle(dep);
    fragNormal = TDOutputSwizzle(nrm);
    fragPos = TDOutputSwizzle(wp);
}
