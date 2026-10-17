// ---- SDF raymarch library (shared by SDF_render, SDF_to_MAT and the node previews) ----
float sdDist(vec3 p){ return sdScene(p).x; }

vec3 sdNormal(vec3 p, float e){
    const vec2 k = vec2(1.0, -1.0);
    return normalize(k.xyy * sdDist(p + k.xyy * e) + k.yyx * sdDist(p + k.yyx * e) +
                     k.yxy * sdDist(p + k.yxy * e) + k.xxx * sdDist(p + k.xxx * e));
}

// sphere tracing; relax < 1 is safer for non-exact fields (twist, noise, repeat). Returns true on hit.
bool sdMarch(vec3 ro, vec3 rd, float tmin, float tmax, int steps, float eps, float relax, out float t, out vec3 alb){
    t = tmin; alb = vec3(0.8);
    for (int i = 0; i < steps; i++){
        vec4 s = sdScene(ro + rd * t);
        if (s.x < eps * (1.0 + 0.5 * t)) { alb = s.yzw; return true; }
        t += s.x * relax;
        if (t > tmax) break;
    }
    return false;
}

float sdShadow(vec3 ro, vec3 rd, float tmin, float tmax, float k){
    float res = 1.0, t = tmin;
    for (int i = 0; i < 48; i++){
        float h = sdDist(ro + rd * t);
        res = min(res, k * h / t);
        t += clamp(h, 0.02, 0.5);
        if (res < 0.001 || t > tmax) break;
    }
    return clamp(res, 0.0, 1.0);
}

float sdAO(vec3 p, vec3 n, float strength){
    float occ = 0.0, sca = 1.0;
    for (int i = 0; i < 5; i++){
        float h = 0.02 + 0.12 * float(i) / 4.0;
        occ += (h - sdDist(p + n * h)) * sca;
        sca *= 0.85;
    }
    return clamp(1.0 - strength * 1.8 * occ, 0.0, 1.0);
}

// key / fill / rim lighting with soft shadow and AO. l = key light direction (towards the light)
vec3 sdLight(vec3 p, vec3 n, vec3 rd, vec3 alb, vec3 l, float shadowk, float aoStrength, vec3 sky){
    float sh = shadowk > 0.0 ? sdShadow(p + n * 0.02, l, 0.02, 12.0, shadowk) : 1.0;
    float ao = aoStrength > 0.0 ? sdAO(p, n, aoStrength) : 1.0;
    float key = max(dot(n, l), 0.0) * sh;
    vec3 lf = normalize(vec3(-l.x, 0.3, -l.z));
    float fill = max(dot(n, lf), 0.0) * 0.25;
    float rim = pow(clamp(1.0 + dot(n, rd), 0.0, 1.0), 3.0) * 0.35;
    float hemi = 0.5 + 0.5 * n.y;
    vec3 h = normalize(l - rd);
    float spec = pow(max(dot(n, h), 0.0), 40.0) * sh * 0.4;
    vec3 col = alb * (vec3(1.0, 0.95, 0.88) * key * 1.2 + vec3(0.55, 0.65, 0.9) * fill + sky * hemi * 0.35 * ao);
    col += rim * mix(vec3(1.0), alb, 0.3) * ao + spec;
    return col * mix(0.6, 1.0, ao);
}

vec3 sdSky(vec3 rd){
    return mix(vec3(0.05, 0.055, 0.07), vec3(0.28, 0.33, 0.42), clamp(rd.y * 0.5 + 0.5, 0.0, 1.0));
}
