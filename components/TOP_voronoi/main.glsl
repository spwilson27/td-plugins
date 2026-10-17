out vec4 fragColor;
vec3 palette(float t){
    if(uD.y > 0.5){   // mono: bone-white / grey cells, accent cells red
        float g = 0.16 + 0.78*fract(t*7.13 + 0.31);
        vec3 c = vec3(g) * vec3(0.96,0.94,0.89);
        float h = fract(sin(floor(t*1000.0)*12.9898)*43758.5453);
        return mix(c, vec3(0.9,0.03,0.03), uD.z*step(0.88, h));
    }
    int id = int(uC.x + 0.5); t += uC.y;
    vec3 a,b,c,d;
    if(id==0){ a=vec3(.5); b=vec3(.5); c=vec3(1.); d=vec3(0.,.33,.67); }
    else if(id==1){ a=vec3(.5,.4,.4); b=vec3(.5,.4,.3); c=vec3(1.,1.,.8); d=vec3(0.,.1,.2); }
    else if(id==2){ a=vec3(.2,.5,.6); b=vec3(.3,.4,.4); c=vec3(1.); d=vec3(0.,.25,.5); }
    else if(id==3){ a=vec3(.5); b=vec3(.5); c=vec3(2.,1.,0.); d=vec3(.5,.2,.25); }
    else return vec3(0.5 + 0.5*cos(6.2831*t)) * vec3(0.9,0.95,1.0);
    return a + b*cos(6.28318*(c*t+d));
}
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
    int N = int(clamp(uA.y, 2., 128.));
    // nearest seed
    float d1 = 1e9; int i1 = 0;
    for(int i=0;i<128;i++){
        if(i>=N) break;
        float d = distance(p, seedPos(i, aspect));
        if(d < d1){ d1 = d; i1 = i; }
    }
    vec2 s1 = seedPos(i1, aspect);
    // border distance
    float bd = 1e9; int i2 = i1;
    for(int j=0;j<128;j++){
        if(j>=N) break;
        if(j==i1) continue;
        vec2 sj = seedPos(j, aspect);
        float b = dot(0.5*(s1+sj) - p, normalize(sj - s1));
        if(b < bd){ bd = b; i2 = j; }
    }
    float bw = uB.x*px;
    float id = hash11(float(i1)*1.37 + uB.w);
    int mode = int(uA.z + 0.5);
    vec3 col;
    vec2 seedUV = clamp(vec2(s1.x/aspect, s1.y), 0.01, 0.99);
    if(mode == 0){            // flat cells
        col = palette(id);
        col *= 0.8 + 0.2*smoothstep(0.3, 0.0, d1);
        col = mix(col*0.35, col, smoothstep(0.0, bw, bd));
    } else if(mode == 1){     // edge glow
        vec3 base = palette(id)*0.10 + texture(sTD2DInputs[0], seedUV).rgb*0.10;
        if(uD.y > 0.5) base = vec3(0.02);
        float g = exp(-bd/(bw*2.0 + 1e-4)*1.5) * uC.z;
        float core = smoothstep(bw*0.5, 0.0, bd);
        vec3 ec = uD.y > 0.5 ? mix(vec3(0.93,0.91,0.86), vec3(0.95,0.03,0.03), uD.z*step(0.85, fract(sin(float(i1)*78.233)*43758.5453))) : palette(id*0.3 + (uD.x > 0.5 ? 0.05*sin(uA.x) : uA.x*0.05));
        col = base + ec*g*1.4 + vec3(1.)*core;
    } else if(mode == 2){     // cracked glass
        vec2 off = (hash21(float(i1)*7.1 + uB.w) - 0.5) * 0.10;
        vec2 uvr = clamp(uv + off*(0.4+0.6*smoothstep(0.,0.3,d1)), 0., 1.);
        col = texture(sTD2DInputs[0], uvr).rgb;
        col *= 0.8 + 0.4*hash11(float(i1)*3.1);
        // subtle gradient to fake facet lighting
        col += (dot(normalize(p - s1 + 1e-5), vec2(0.6,0.8))*0.06) * (hash11(float(i1)*9.)-0.3);
        float crack = smoothstep(bw*0.6, 0.0, bd);
        float hl = smoothstep(bw*1.8, bw*0.6, bd) * (1.-crack);
        col = col*(1.-crack*0.9) + hl*0.18 + crack*0.0;
        // fine secondary hairline cracks radiating from seeds
        float ang = atan(p.y - s1.y, p.x - s1.x);
        float rad = abs(sin(ang*5. + id*30.)) ;
        float hair = smoothstep(0.02, 0., rad) * smoothstep(0.15, 0.0, d1) * 0.25;
        col *= 1. - hair;
    } else {                  // stained glass
        vec3 c0 = texture(sTD2DInputs[0], seedUV).rgb;
        float l = dot(c0, vec3(.299,.587,.114));
        c0 = clamp(mix(vec3(l), c0, 1.5), 0., 1.) * (0.75 + 0.5*hash11(float(i1)*5.3));
        c0 *= 0.7 + 0.5*smoothstep(0.35, 0.0, d1);
        float lead = smoothstep(bw*0.6, bw*0.35, bd);
        col = mix(c0, vec3(0.03,0.03,0.035), lead);
        col += vec3(1.0,0.9,0.7) * smoothstep(0.02,0.0,d1)*0.4;
    }
    // Delaunay overlay (Gabriel graph edges), drawn for the edges of the pixel's own cell
    if(uA.w > 0.5){
        float ld = 1e9;
        for(int j=0;j<128;j++){
            if(j>=N) break;
            if(texelFetch(sTD2DInputs[1], ivec2(i1, j), 0).r > 0.5)
                ld = min(ld, segDist(p, s1, seedPos(j, aspect)));
        }
        float lw = uC.w*px;
        float line = smoothstep(lw, lw*0.4, ld);
        col = mix(col, vec3(1.0, 0.95, 0.8), line*0.9);
        col = mix(col, vec3(1.), smoothstep(0.006, 0.003, d1));
    }
    if(uD.y > 0.5 && mode >= 2){ float l = dot(col, vec3(.299,.587,.114)); col = vec3(l*l*1.3) * vec3(0.96,0.94,0.89); }
    fragColor = TDOutputSwizzle(vec4(col, 1.));
}
