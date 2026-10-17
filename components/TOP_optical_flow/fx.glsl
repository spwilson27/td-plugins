// in0 source, in1 flow (rg = uv displacement per frame), in2 previous output
uniform vec4 uA; // x mode (0 smear,1 warp,2 viz)  y gain  z persistence  w active
out vec4 fragColor;
vec3 hsv2rgb(vec3 c){ vec3 k=clamp(abs(fract(c.x+vec3(0.,2./3.,1./3.))*6.-3.)-1.,0.,1.); return c.z*mix(vec3(1.),k,c.y); }
void main(){
  vec2 uv=vUV.st;
  vec2 v=texture(sTD2DInputs[1],uv).xy;
  vec4 prev=texture(sTD2DInputs[2],uv);
  if(uA.w<.5){ fragColor=TDOutputSwizzle(prev); return; }
  int mode=int(uA.x+.5);
  vec3 s=texture(sTD2DInputs[0],uv).rgb;
  vec3 c;
  if(mode==0){            // advect feedback along the flow, re-inject source
    vec3 pa=texture(sTD2DInputs[2],uv-v*uA.y).rgb;
    float m=length(v*uTDOutputInfo.res.zw);
    c=mix(s,pa,uA.z*clamp(.5+m,0.,1.));
    c=max(c,s*.0);
  } else if(mode==1){     // warp source by flow
    c=texture(sTD2DInputs[0],uv-v*uA.y*8.).rgb;
  } else {                // HSV visualisation: hue = direction, value = speed
    float a=atan(v.y,v.x)/6.2831853+.5;
    float m=length(v*uTDOutputInfo.res.zw);
    c=hsv2rgb(vec3(a,1.,1.-exp(-m*uA.y*.6)))+s*.12;
  }
  fragColor=TDOutputSwizzle(vec4(c,1.));
}
