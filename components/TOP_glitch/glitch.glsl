// in0 = source, in1 = previous output (feedback)
uniform vec4 uG;   // x global amount, y seed, z time, w rate (beats/sec)
uniform vec4 uA;   // x rgb split, y block displace, z scanline tear, w pixel sort
uniform vec4 uB;   // x smear amount, y smear threshold, z sort threshold, w sort axis (0 horiz, 1 vert)
uniform vec4 uC;   // x block size px (smear + displacement grid scale), y active
out vec4 fragColor;
float hash11(float p){ p=fract(p*.1031); p*=p+33.33; p*=p+p; return fract(p); }
float hash21(vec2 p){ vec3 p3=fract(vec3(p.xyx)*.1031); p3+=dot(p3,p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
float luma(vec3 c){ return dot(c,vec3(.299,.587,.114)); }
vec3 S(vec2 uv){ return texture(sTD2DInputs[0],uv).rgb; }

void main(){
  vec2 uv=vUV.st;
  vec2 px=uTDOutputInfo.res.xy;
  vec4 prev=texture(sTD2DInputs[1],uv);
  if(uC.y<.5){ fragColor=TDOutputSwizzle(prev); return; }
  float G=uG.x, seed=uG.y*13.37;
  // phase mode: tb runs 0..K (K integer glitch ticks per loop) so the event sequence repeats exactly
  float tb=uG.z*uG.w;
  float beat=(uC.z>.5 ? mod(floor(tb),max(uC.w,1.)) : floor(tb))+seed;
  float ph=fract(tb);
  float env=1.-smoothstep(0.,.6,ph);          // decays after each beat
  vec2 w=uv;                                  // warped lookup

  // --- block displacement: random blocks shift per beat
  float ba=uA.y*G;
  if(ba>0.){
    vec2 grid=vec2(mix(6.,28.,hash11(beat*1.3)),mix(4.,16.,hash11(beat*2.1)));
    vec2 id=floor(uv*grid);
    float r=hash21(id+beat*7.7);
    if(r<ba*.6){
      vec2 o=vec2(hash21(id+beat*3.1)-.5,hash21(id+beat*5.3)-.5);
      w+=o*.35*ba*(.4+.6*env+.3);
    }
  }
  // --- scanline tear
  float ta=uA.z*G;
  if(ta>0.){
    float rows=mix(40.,160.,hash11(beat*.71));
    float row=floor(uv.y*rows);
    float r=hash21(vec2(row,beat));
    if(r>1.-ta*.35) w.x+=(hash21(vec2(row,beat+9.))-.5)*ta*.5;
    // wide rolling tear band
    float by=fract(beat*.37+tb*(uC.z>.5 ? max(1.,floor(uC.w*.1+.5))/max(uC.w,1.) : .1));
    float inb=step(abs(uv.y-by),.02+.05*ta);
    w.x+=inb*ta*.15*sin(uv.y*400.+beat);
  }
  // --- rgb split
  float sa=uA.x*G;
  float ang=hash11(beat*3.3)*6.2831;
  vec2 d=vec2(cos(ang),sin(ang))*sa*.03*(.5+env);
  vec3 c=vec3(S(w+d).r,S(w).g,S(w-d).b);

  // --- approximate pixel sort: streaks of above-threshold pixels along an axis
  float pa=uA.w*G;
  if(pa>0.){
    vec2 dir=uB.w<.5?vec2(px.x,0.):vec2(0.,px.y);
    float lane=uB.w<.5?floor(uv.y*180.):floor(uv.x*320.);
    float maxN=6.+floor(hash21(vec2(lane,beat))*42.);
    float thr=uB.z;
    float l0=luma(c);
    if(l0>thr && hash21(vec2(lane,beat+2.))<pa*1.4){
      vec3 best=c; float bl=l0; int n=0;
      vec3 start=c;
      for(int i=1;i<=48;i++){
        if(float(i)>maxN) break;
        vec3 s=S(w-dir*float(i)*3.);
        float ls=luma(s);
        if(ls<=thr) break;
        start=s; n=i;
        if(ls>bl){ bl=ls; best=s; }
      }
      float t=float(n)/maxN;
      c=mix(c,mix(start,best,smoothstep(0.,1.,t)),clamp(pa*1.5,0.,1.));
    }
  }

  // --- fake compression smear: hold previous output where motion is low (per-block)
  float ma=uB.x*G;
  if(ma>0.){
    vec2 bs=px*uC.x;
    vec2 bc=(floor(uv/bs)+.5)*bs;
    vec3 cs=S(bc); vec3 ps=texture(sTD2DInputs[1],bc).rgb;
    float diff=length(cs-ps);
    float hold=1.-smoothstep(uB.y*.5,uB.y,diff);
    float key=step(hash11(beat*9.1),.08);   // occasional keyframe refresh
    hold*=(1.-key);
    // motion regions drag old pixels along (mosh)
    c=mix(c,prev.rgb,hold*clamp(ma,0.,1.));
  }
  fragColor=TDOutputSwizzle(vec4(c,1.));
}
