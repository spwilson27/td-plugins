// TOP_env_reflect. in0 = colour, in1 = view-space normals, in2 = equirect env map, in3 = mask (R).
out vec4 fragColor;
uniform vec4 uA;   // fov (deg, 0 = orthographic view), roughness, reflectivity, fresnel mix
uniform vec4 uB;   // ior, refraction amount, mode (0 chrome, 1 glass), mask mode (0 roughness, 1 reflectivity, 2 off)
uniform vec4 uC;   // env yaw (rad), env tilt (rad), normal encoding (0 signed, 1 packed), env gain
uniform vec4 uD;   // tint rgb, -

void main(){
    vec2 uv = vUV.st;
    vec4 col = texture(sTD2DInputs[0], uv);
    vec3 nr = texture(sTD2DInputs[1], uv).rgb;
    if (uC.z > 0.5) nr = nr * 2.0 - 1.0;
    if (dot(nr, nr) < 0.01) { fragColor = TDOutputSwizzle(col); return; }
    vec3 n = normalize(nr);

    vec3 I = vec3(0.0, 0.0, -1.0);
    if (uA.x > 0.5) {
        float asp = uTDOutputInfo.res.z / uTDOutputInfo.res.w;
        float th = tan(radians(uA.x) * 0.5);
        I = normalize(vec3((uv.x * 2.0 - 1.0) * th * asp, (uv.y * 2.0 - 1.0) * th, -1.0));
    }
    float nv = clamp(dot(n, -I), 0.0, 1.0);
    vec3 R = reflect(I, n);
    float ct = cos(uC.y), st = sin(uC.y);
    R = vec3(R.x, ct * R.y - st * R.z, st * R.y + ct * R.z);          // tilt about X
    float cy = cos(uC.x), sy = sin(uC.x);
    R = vec3(cy * R.x + sy * R.z, R.y, -sy * R.x + cy * R.z);          // yaw about Y
    vec2 euv = vec2(atan(R.x, -R.z) / 6.2831853 + 0.5, asin(clamp(R.y, -1.0, 1.0)) / 3.1415927 + 0.5);

    float mk = (uB.w < 1.5) ? texture(sTD2DInputs[3], uv).r : 1.0;
    float rough = clamp(uA.y * (uB.w < 0.5 ? mk : 1.0), 0.0, 1.0);
    float maxlod = log2(float(max(textureSize(sTD2DInputs[2], 0).x, 2)));
    vec3 env = textureLod(sTD2DInputs[2], euv, rough * maxlod * 0.85).rgb * uC.w;

    float f0 = pow((uB.x - 1.0) / (uB.x + 1.0), 2.0);
    float fr = f0 + (1.0 - f0) * pow(1.0 - nv, 5.0);
    float w = mix(uA.z, fr, uA.w);
    if (uB.w > 0.5 && uB.w < 1.5) w *= mk;
    w = clamp(w, 0.0, 1.0);

    vec3 rgb;
    if (uB.z < 0.5) {
        rgb = mix(col.rgb, env * uD.rgb, w);
    } else {
        vec2 off = n.xy * (1.0 - 1.0 / uB.x) * uB.y * 0.12;                 // screen-space refraction offset
        vec3 trans = texture(sTD2DInputs[0], uv - off).rgb * uD.rgb;
        rgb = mix(trans, env, w);
    }
    fragColor = TDOutputSwizzle(vec4(rgb, col.a));
}
