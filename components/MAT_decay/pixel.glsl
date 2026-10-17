// mat_decay: clean steel -> rust -> pitted corrosion. Object-space triplanar noise + curvature-derived cavity. No UVs.
uniform vec4 uD0; // x=decay 0..1, y=scale, z=cavity strength, w=pit amount
uniform vec4 uD1; // x=curvature bias (1/units), y=edge wear, z=relief, w=pit size
uniform vec4 uMetal; // rgb clean metal albedo
uniform vec4 uRust1; // rgb orange rust
uniform vec4 uRust2; // rgb dark rust / pits

out vec4 oFragColor;

// triplanar fbm in object space (planar projections blended by the object-space normal)
float triFbm(vec3 p, vec3 nO, vec3 stretch){
  vec3 w = pow(abs(nO), vec3(4.0)); w /= (w.x + w.y + w.z + 1e-4);
  float a = fbm(vec3(p.yz*stretch.yz, 3.3));
  float b = fbm(vec3(p.xz*stretch.xz, 7.7));
  float c = fbm(vec3(p.xy*stretch.xy, 1.9));
  return a*w.x + b*w.y + c*w.z;
}

void main(){
  TDCheckDiscard();
  float decay = uD0.x, scl = uD0.y, cavK = uD0.z, pitAmt = uD0.w;
  float cbias = uD1.x, edgeK = uD1.y, relief = uD1.z, pitSize = uD1.w;

  vec3 N = normalize(vv.wN);
  vec3 V = normalize(vv.cam - vv.wP);
  if(dot(N,V) < 0.0) N = -N;
  vec3 p = vv.oP*scl;
  vec3 nO = normalize(vv.oN);

  // ---- curvature (mean, world units, + convex) from screen-space derivatives -> cavity / edge masks ----
  vec3 dNx = dFdx(N), dNy = dFdy(N), dPx = dFdx(vv.wP), dPy = dFdy(vv.wP);
  float curv = (dot(dNx,dPx) + dot(dNy,dPy))/(dot(dPx,dPx) + dot(dPy,dPy) + 1e-8);
  float cavityC = sat((cbias - curv)/max(cbias,0.3));          // concave / flatter regions collect rust
  float edgeC = sat((curv - cbias*2.0)/(cbias*2.0 + 0.5));     // convex edges wear back to metal

  // ---- weathering masks ----
  float m1 = triFbm(p, nO, vec3(1.0));
  float m2 = triFbm(p*1.0 + 5.0, nO, vec3(2.6, 0.45, 2.6));    // vertical drip streaks
  float grain = triFbm(p*9.0 + 2.0, nO, vec3(1.0));
  float lowH = 1.0 - triFbm(p*2.3 + 9.0, nO, vec3(1.0));       // low spots
  float score = m1*0.62 + m2*0.25 + lowH*0.13 + cavityC*cavK*0.45 - edgeC*edgeK*0.5;
  float thr = 1.1 - decay*1.45;                                  // decay sweeps threshold across the score field
  float rust = smoothstep(thr, thr + 0.16, score);
  float film = smoothstep(thr - 0.20, thr + 0.02, score);       // faint orange bloom before real rust forms
  rust = sat(rust);

  // ---- pitting (stage 2): dimples inside rusted areas, growing with decay ----
  float pitStage = sat((decay - 0.40)*1.8)*pitAmt;
  vec2 vf = voro(p*(3.0/max(pitSize,0.1)) + 4.0);
  float dimples = 1.0 - smoothstep(0.0, 0.42, vf.x);
  float pitMaskN = smoothstep(0.35, 0.7, triFbm(p*1.3 + 21.0, nO, vec3(1.0)) + (pitStage - 0.5)*0.5);
  float pit = dimples*pitMaskN*rust*pitStage;
  float pit2 = (1.0 - smoothstep(0.0, 0.3, voro(p*(9.0/max(pitSize,0.1)) + 13.0).x))*rust*pitStage*smoothstep(0.4,0.7,grain);
  pit = sat(max(pit, pit2*0.8));

  // ---- albedo / material response ----
  vec3 steel = uMetal.rgb*(0.82 + 0.3*grain);
  float scratch = vnoise(vec3(p.x*60.0, p.y*2.0, p.z*60.0));
  steel *= 0.9 + 0.2*scratch;
  vec3 rustCol = mix(uRust1.rgb, uRust2.rgb, sat(triFbm(p*3.5 + 31.0, nO, vec3(1.0))*1.2 - 0.2 + decay*0.35));
  rustCol *= 0.7 + 0.6*grain;
  vec3 albedo = mix(steel, steel*vec3(1.0,0.72,0.55) , film*0.5*(1.0 - rust));
  albedo = mix(albedo, rustCol, rust);
  albedo = mix(albedo, uRust2.rgb*0.25, pit);
  float metal = sat(1.0 - rust*0.92 - film*0.2) * (1.0 - pit);
  float rough = mix(0.26 + 0.12*grain, 0.82, rust);
  rough = mix(rough, 0.95, pit);
  rough = clamp(rough + film*0.15, 0.05, 1.0);

  // ---- relief: rust blisters up a little, pits sink ----
  float hgt = rust*(0.25 + 0.35*grain) - pit*1.2 + (grain - 0.5)*0.12;
  vec3 Nb = bumpDeriv(N, hgt*0.012*relief, 1.0);
  float ao = 1.0 - pit*0.65 - cavityC*cavK*rust*0.25;

  vec3 col = shadePBR(Nb, V, albedo, metal, rough, ao);
  oFragColor = TDOutputSwizzle(vec4(col, 1.0));
}
