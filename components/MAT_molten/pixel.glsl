// mat_molten: glowing lava cracks through a dark cooling crust. Object-space, loopable.
uniform vec4 uM0; // x=crack width, y=cooling, z=heat (emission gain), w=crack scale
uniform vec4 uM1; // x=flow (domain warp), y=pulse, z=crust bump, w=detail streaks
uniform vec4 uCrust; // rgb crust color
uniform vec4 uGlow;  // rgb glow tint multiplier

out vec4 oFragColor;

// blackbody-ish temperature ramp, t = 0..1+
vec3 tempRamp(float t){
  t = max(t, 0.0);
  vec3 c = vec3(0.0);
  c = mix(c, vec3(0.30,0.012,0.0), smoothstep(0.00,0.22,t));
  c = mix(c, vec3(0.95,0.14,0.01), smoothstep(0.20,0.50,t));
  c = mix(c, vec3(1.00,0.52,0.06), smoothstep(0.45,0.75,t));
  c = mix(c, vec3(1.00,0.88,0.45), smoothstep(0.70,1.00,t));
  c = mix(c, vec3(1.00,1.00,0.95), smoothstep(1.00,1.40,t));
  return c*smoothstep(0.0,0.12,t);
}

void main(){
  TDCheckDiscard();
  float ph = uEnv.z;
  float wdth = uM0.x, cool = uM0.y, heat = uM0.z, scl = uM0.w;
  float flow = uM1.x, pulse = uM1.y, bump = uM1.z, streaks = uM1.w;

  vec3 p = vv.oP*scl;
  vec3 N = normalize(vv.wN);
  vec3 V = normalize(vv.cam - vv.wP);
  if(dot(N,V) < 0.0) N = -N;

  // flowing domain warp (periodic: circular paths through noise space)
  vec3 o1 = loopOff(ph, 1.0, 0.9), o2 = loopOff(ph, 1.0, 0.9).yzx*vec3(1,-1,1);
  vec3 w = vec3(fbm(p*0.7 + o1), fbm(p*0.7 + 5.2 + o2), fbm(p*0.7 + 9.1 - o1));
  vec3 q = p + (w - 0.5)*flow*2.2;

  // crack network: edges of an orbiting voronoi
  vec2 f = voroA(q, ph);
  float e = f.y - f.x;
  vec2 f2 = voroA(q*2.3 + 3.7, ph);
  float e2 = f2.y - f2.x;
  float cw = mix(0.02, 0.30, wdth)*(1.0 - cool*0.75);
  float crack = 1.0 - smoothstep(0.0, cw, e);
  float crack2 = (1.0 - smoothstep(0.0, cw*0.6, e2))*smoothstep(0.35,0.9,fbm2(q*1.3 + 7.0));
  float net = max(crack, crack2*0.8);
  float halo = exp(-e/(cw*1.6 + 1e-3));

  // molten temperature: hot cores, noisy streaks flowing in the crack, pulsing
  float hot = fbm(q*1.8 + loopOff(ph, 1.0, 1.2));
  float stk = fbm(q*vec3(3.0,7.0,3.0) + loopOff(ph, 2.0, 1.4)*streaks);
  float T = net*(0.40 + 0.55*hot)*mix(1.0, 0.55 + 0.9*stk, streaks);
  T += halo*0.12*(0.6 + 0.8*hot);
  T *= (1.0 - cool*0.80);
  float pulseK = 1.0 + pulse*0.35*sin(TAU*ph*2.0);
  vec3 emit = tempRamp(T*1.15)*uGlow.rgb*heat*pulseK;
  emit *= mix(1.0, 0.25 + 0.75*net, 0.6);                 // glow concentrated in the cracks

  // cooling crust: dark basalt, ash patches when cooler, raised plates
  float n1 = fbm(vv.oP*6.0 + 4.0), n2 = fbm(vv.oP*22.0);
  vec3 crust = uCrust.rgb*(0.6 + 0.8*n1)*(0.75 + 0.5*n2);
  crust = mix(crust, vec3(0.16,0.15,0.145)*(0.7+0.6*n2), cool*0.5*smoothstep(0.35,0.75,n1));
  crust = mix(crust, crust*0.25, net);
  // crust is warmly lit by the lava next to it
  vec3 lavaLight = tempRamp(0.5)*uGlow.rgb*heat*pow(halo,2.0)*0.12*(1.0 - cool*0.8);
  float hgt = smoothstep(0.0, cw*3.0, e)*0.9 + n2*0.35 + n1*0.2;
  vec3 Nb = bumpDeriv(N, hgt*0.02*(0.2+bump*2.0), 1.0);
  float ao = mix(0.35, 1.0, smoothstep(0.0, cw*3.5, e));
  vec3 col = shadePBR(Nb, V, crust, 0.0, 0.78 - 0.2*smoothstep(0.4,0.8,n1)*cool, ao);
  col += crust*lavaLight*3.0;
  col = mix(col, vec3(0.0), net*0.8) + emit;
  oFragColor = TDOutputSwizzle(vec4(col, 1.0));
}
