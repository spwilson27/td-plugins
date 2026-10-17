vec4 sdf_@ID@(vec3 p){
    vec4 a = P_@ID@_0, b = P_@ID@_3;
    int ty = int(a.x + 0.5), it = int(a.y + 0.5);
    float sz = a.w;
    vec3 q = p / sz;
    float d = 0.0, trap = 1.0;
    if (ty == 0){                      // mandelbulb
        vec3 w = q; float m = dot(w, w), dz = 1.0, pw = a.z; trap = m;
        for (int i = 0; i < 16; i++){
            if (i >= it) break;
            dz = pw * pow(m, (pw - 1.0) * 0.5) * dz + 1.0;
            float r = length(w);
            float th = acos(clamp(w.y / r, -1.0, 1.0)) * pw, ph = atan(w.x, w.z) * pw;
            w = q + pow(r, pw) * vec3(sin(th) * sin(ph), cos(th), sin(th) * cos(ph));
            m = dot(w, w); trap = min(trap, m);
            if (m > 256.0) break;
        }
        d = 0.25 * log(m) * sqrt(m) / dz;
        trap = clamp(sqrt(trap), 0.0, 1.0);
    } else if (ty == 1){               // menger sponge
        vec3 aq = abs(q);
        d = max(aq.x, max(aq.y, aq.z)) - 1.0;
        float s = 1.0; trap = 0.0;
        for (int i = 0; i < 8; i++){
            if (i >= it) break;
            vec3 aa = mod(q * s, 2.0) - 1.0;
            s *= a.z;
            vec3 r = abs(1.0 - a.z * abs(aa));
            float da = max(r.x, r.y), db = max(r.y, r.z), dc = max(r.z, r.x);
            float c = (min(da, min(db, dc)) - 1.0) / s;
            if (c > d) { d = c; trap = float(i + 1) / float(it); }
        }
    } else {                           // kaleidoscopic IFS
        vec3 w = q; float s = a.z; trap = 1e3;
        float ca = cos(b.w), sa = sin(b.w);
        for (int i = 0; i < 16; i++){
            if (i >= it) break;
            w = abs(w);
            if (w.x < w.y) w.xy = w.yx;
            if (w.x < w.z) w.xz = w.zx;
            if (w.y < w.z) w.yz = w.zy;
            w = w * s - b.xyz * (s - 1.0);
            w.xy = mat2(ca, -sa, sa, ca) * w.xy;
            trap = min(trap, dot(w, w));
        }
        d = (length(w) - 1.0) * pow(s, -float(it));
        trap = clamp(sqrt(trap) * 0.15, 0.0, 1.0);
    }
    return vec4(d * sz, mix(P_@ID@_1.xyz, P_@ID@_2.xyz, trap));
}
