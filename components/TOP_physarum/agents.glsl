// Physarum agent update. State: r=x(uv) g=y(uv) b=heading(rad) a=alive flag.
uniform vec4 uP;   // x=sensorAngle(rad) y=sensorDist(px) z=turnSpeed(rad) w=step(px)
uniform vec4 uQ;   // x=reset y=play z=time(frame) w=init pattern
uniform vec4 uA;   // x=attraction (input field strength, may be negative) y=seed
out vec4 fragColor;

float hash(vec2 p){ p = fract(p*vec2(443.897,441.423)); p += dot(p,p.yx+19.19); return fract((p.x+p.y)*p.x); }

// sensed value = own trail + input-image attractor field (in2)
float sense(vec2 p){
    p = fract(p);
    return texture(sTD2DInputs[1], p).r + uA.x*texture(sTD2DInputs[2], p).r;
}

void main(){
    ivec2 ip = ivec2(gl_FragCoord.xy);
    vec4 a = texelFetch(sTD2DInputs[0], ip, 0);
    vec2 res = uTDOutputInfo.res.zw;           // agent tex size (unused for px)
    vec2 trailRes = vec2(textureSize(sTD2DInputs[1], 0));
    vec2 seed = vec2(ip) + 0.5 + uA.y*37.31;
    if (uQ.x > 0.5 || a.w < 0.5) {
        float h1 = hash(seed), h2 = hash(seed+7.1), h3 = hash(seed+13.7);
        vec2 p; float h;
        if (uQ.w < 0.5) { p = vec2(h1,h2); h = h3*6.2831853; }
        else if (uQ.w < 1.5) { // disc, heading inward
            float r = 0.38*sqrt(h1), t = h2*6.2831853;
            p = vec2(0.5) + r*vec2(cos(t)*trailRes.y/trailRes.x, sin(t)); h = t+3.14159265;
        } else { // ring, heading outward
            float t = h2*6.2831853, r = 0.3+0.02*h1; p = vec2(0.5) + r*vec2(cos(t)*trailRes.y/trailRes.x, sin(t)); h = t;
        }
        fragColor = vec4(p, h, 1.0); return;
    }
    if (uQ.y < 0.5) { fragColor = a; return; }
    vec2 pos = a.xy; float h = a.z;
    float sa = uP.x, sd = uP.y, ts = uP.z, st = uP.w;
    vec2 ipx = 1.0/trailRes;
    float f  = sense(pos + vec2(cos(h),    sin(h))*sd*ipx);
    float fl = sense(pos + vec2(cos(h+sa),  sin(h+sa))*sd*ipx);
    float fr = sense(pos + vec2(cos(h-sa),  sin(h-sa))*sd*ipx);
    float rnd = hash(seed + uQ.z*0.01);
    if (f > fl && f > fr) { }
    else if (f < fl && f < fr) { h += (rnd-0.5)*2.0*ts; }
    else if (fl > fr) { h += ts; }
    else if (fr > fl) { h -= ts; }
    pos += vec2(cos(h), sin(h))*st*ipx;
    pos = fract(pos);
    fragColor = vec4(pos, h, 1.0);
}
