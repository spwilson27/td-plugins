uniform vec4 uA; // style (0 cells 1 edges 2 cracked 3 stained), borderwidth px, glow, displace
uniform vec4 uB; // delaunay, linewidth px, mix, beat flash
uniform vec4 uC; // mono look, accent, count, edge tint
uniform vec4 uD; // edge colour rgb, 0
out vec4 fragColor;
float hash11(float n){ return fract(sin(n*127.1+311.7)*43758.5453); }
vec2 hash21(float n){ return vec2(hash11(n), hash11(n+17.31)); }
float lum(vec3 c){ return dot(c, vec3(.299,.587,.114)); }
float segDist(vec2 p, vec2 a, vec2 b){
    vec2 pa = p-a, ba = b-a; float h = clamp(dot(pa,ba)/dot(ba,ba), 0., 1.);
    return length(pa - ba*h);
}
void main(){
    vec2 res = uTDOutputInfo.res.zw;
    float aspect = res.x/res.y;
    vec2 uv = vUV.st;
    vec2 p = vec2(uv.x*aspect, uv.y);
    float px = 1.0/res.y;
    vec4 src = texture(sTD2DInputs[0], uv);
    vec4 cell = texelFetch(sTD2DInputs[2], ivec2(gl_FragCoord.xy), 0);
    int i1 = int(cell.x + 0.5), i2 = int(cell.y + 0.5);
    float d1 = cell.z, bd = cell.w;
    vec2 s1 = texelFetch(sTD2DInputs[1], ivec2(i1,0), 0).xy;
    float id = texelFetch(sTD2DInputs[1], ivec2(i1,0), 0).z;
    vec3 c1 = texelFetch(sTD2DInputs[1], ivec2(i1,1), 0).rgb;
    vec3 c2 = texelFetch(sTD2DInputs[1], ivec2(i2,1), 0).rgb;
    float cs = sqrt(aspect/max(uC.z,1.));          // typical cell size
    float bw = uA.y*px;
    int style = int(uA.x + 0.5);
    vec3 col;
    if(style == 0){            // flat cells
        col = c1 * (0.9 + 0.2*hash11(id*40.));
        col *= 0.85 + 0.25*smoothstep(cs*0.8, 0.0, d1);
        col = mix(col*0.25, col, smoothstep(0.0, bw, bd));
    } else if(style == 1){     // glowing edges over a dimmed image
        vec3 base = mix(src.rgb, c1, 0.5)*0.22;
        vec3 ec = 0.5*(c1 + c2);
        ec = ec / max(max(ec.r, max(ec.g, ec.b)), 0.25);
        ec = mix(uD.rgb, ec, uC.w);
        float g = exp(-bd/(bw*2.0 + 1e-4)*1.5) * uA.z;
        float core = smoothstep(bw*0.5, 0.0, bd);
        col = base + ec*g*(1.2 + uB.w) + uD.rgb*core;
    } else if(style == 2){     // cracked glass: every shard shows a shifted piece of the input
        vec2 off = (hash21(id*70.1) - 0.5) * 0.4 * uA.w;
        vec2 uvr = clamp(uv + off*(0.4+0.6*smoothstep(0., cs*0.6, d1)), 0.001, 0.999);
        col = texture(sTD2DInputs[0], uvr).rgb;
        col *= 0.8 + 0.4*hash11(id*31.);
        col += (dot(normalize(p - s1 + 1e-5), vec2(0.6,0.8))*0.06) * (hash11(id*91.)-0.3);
        float crack = smoothstep(bw*0.6, 0.0, bd);
        float hl = smoothstep(bw*1.8, bw*0.6, bd) * (1.-crack);
        col = col*(1.-crack*0.9) + hl*0.18*(1.+uB.w);
        float ang = atan(p.y - s1.y, p.x - s1.x);
        float rad = abs(sin(ang*5. + id*30.));
        col *= 1. - smoothstep(0.02, 0., rad) * smoothstep(cs*0.5, 0.0, d1) * 0.25;
    } else {                   // stained glass
        float l = lum(c1);
        vec3 c0 = clamp(mix(vec3(l), c1, 1.5), 0., 1.) * (0.75 + 0.5*hash11(id*50.3));
        c0 *= 0.7 + 0.5*smoothstep(cs*0.7, 0.0, d1);
        float lead = smoothstep(bw*0.6, bw*0.35, bd);
        col = mix(c0, vec3(0.03,0.03,0.035), lead);
        col += vec3(1.0,0.9,0.7) * smoothstep(px*3., 0.0, d1)*0.4;
    }
    if(uB.x > 0.5){            // Delaunay (Gabriel) overlay
        float ld = 1e9;
        for(int j=0;j<128;j++){
            if(j>=int(uC.z)) break;
            if(texelFetch(sTD2DInputs[3], ivec2(i1, j), 0).r > 0.5)
                ld = min(ld, segDist(p, s1, texelFetch(sTD2DInputs[1], ivec2(j,0), 0).xy));
        }
        float lw = uB.y*px;
        col = mix(col, vec3(1.0, 0.95, 0.8), smoothstep(lw, lw*0.4, ld)*0.9);
        col = mix(col, vec3(1.), smoothstep(px*4., px*2., d1));
    }
    if(uC.x > 0.5){            // Mono look: bone-white / grey, optional red accent cells
        float l = lum(col);
        col = vec3(l) * vec3(0.96,0.94,0.89);
        col = mix(col, vec3(0.9,0.03,0.03)*(0.3+l), uC.y*step(0.85, hash11(id*77.7)));
    }
    col = mix(src.rgb, col, uB.z);
    fragColor = TDOutputSwizzle(vec4(col, 1.));
}
