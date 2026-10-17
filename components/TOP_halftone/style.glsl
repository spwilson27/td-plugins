// in0 source, in1 glyph atlas (10 cells)
uniform vec4 uA; // x mode (0 halftone,1 dither,2 ascii)  y sub type  z cell size px  w angle rad
uniform vec4 uB; // x softness  y levels  z keep colour (ascii/dither mono=0)  w mix
uniform vec4 uC; // ink rgb, w invert
uniform vec4 uD; // paper rgb, w dither mono
out vec4 fragColor;
vec3 src(vec2 uv){ return clamp(texture(sTD2DInputs[0],uv).rgb,0.,1.); }
float luma(vec3 c){ return dot(c,vec3(.299,.587,.114)); }
float bayer(ivec2 p,int bits){
  int v=0; int n=1<<bits; p=ivec2(p.x&(n-1),p.y&(n-1));
  for(int i=0;i<3;i++){ if(i>=bits) break;
    int xi=(p.x>>i)&1, yi=(p.y>>i)&1; v=v*4+((xi^yi)*2+yi); }
  int r=v;
  return (float(r)+.5)/float(n*n);
}
float ign(vec2 p){ return fract(52.9829189*fract(dot(p,vec2(.06711056,.00583715)))); }
float r2(vec2 p){ return fract(dot(p,vec2(.7548776662,.56984029))); }
mat2 rot(float a){ float c=cos(a),s=sin(a); return mat2(c,-s,s,c); }

float screenMask(vec2 f,float cov,float aa){
  float r=sqrt(clamp(cov,0.,1.))*.7071;
  return 1.-smoothstep(r-aa,r+aa,length(f)); }
vec4 cmyk(vec3 c){ float k=1.-max(c.r,max(c.g,c.b)); vec3 cm=(vec3(1.)-c-k)/max(1.-k,1e-3); return vec4(cm,k); }

void main(){
  vec2 uv=vUV.st; vec2 res=uTDOutputInfo.res.zw;
  vec2 pix=uv*res;
  int mode=int(uA.x+.5); int sub=int(uA.y+.5);
  float cs=max(uA.z,2.);
  vec3 orig=src(uv);
  vec3 outc=orig;
  float aa=max(uB.x,.02);
  if(mode==0){
    if(sub==0){ // CMYK
      float angs[4]=float[4](.2618,1.309,0.,.7854);
      vec3 inks[4]=vec3[4](vec3(0.,.66,.92),vec3(.93,0.,.55),vec3(1.,.93,0.),vec3(.08,.08,.09));
      vec3 paper=uD.rgb; vec3 col=paper;
      for(int k=0;k<4;k++){
        mat2 R=rot(angs[k]+uA.w);
        vec2 p=R*pix/cs; vec2 id=floor(p)+.5; vec2 f=p-id;
        vec2 cp=transpose(R)*(id*cs);
        vec4 cm=cmyk(src(cp/res));
        float cov=k==0?cm.x:(k==1?cm.y:(k==2?cm.z:cm.w));
        float m=screenMask(f,cov,aa*.5);
        col*=mix(vec3(1.),inks[k],m);
      }
      outc=col;
    } else { // mono dot screen
      mat2 R=rot(uA.w);
      vec2 p=R*pix/cs; vec2 id=floor(p)+.5; vec2 f=p-id;
      vec2 cp=transpose(R)*(id*cs);
      float l=luma(src(cp/res));
      if(uC.w>.5) l=1.-l;
      float m=screenMask(f,1.-l,aa*.5);
      outc=mix(uD.rgb,uC.rgb,m);
    }
  } else if(mode==1){
    float ps=cs; vec2 blk=floor(pix/ps); vec2 cuv=(blk+.5)*ps/res;
    vec3 s=src(cuv);
    float L=max(uB.y,2.)-1.;
    float thr;
    if(sub==0) thr=bayer(ivec2(blk),1);
    else if(sub==1) thr=bayer(ivec2(blk),2);
    else if(sub==2) thr=bayer(ivec2(blk),3);
    else if(sub==3) thr=ign(blk);
    else thr=r2(blk);
    if(uD.w>.5){
      float l=luma(s); float q=floor(l*L+thr)/L;
      outc=mix(uC.rgb,uD.rgb,clamp(q,0.,1.));
    } else {
      outc=floor(s*L+vec3(thr))/L;
    }
  } else {
    vec2 cell=floor(pix/cs); vec2 loc=fract(pix/cs);
    vec2 c0=(cell+.5)*cs/res; vec2 o=.25*cs/res;
    vec3 avg=(src(c0+vec2(-o.x,-o.y))+src(c0+vec2(o.x,-o.y))+src(c0+vec2(-o.x,o.y))+src(c0+vec2(o.x,o.y)))*.25;
    float l=luma(avg); if(uC.w>.5) l=1.-l;
    float idx=floor(clamp(l,0.,.999)*10.);
    float g=texture(sTD2DInputs[1],vec2((idx+loc.x)/10.,loc.y)).r;
    vec3 fg=uB.z>.5?avg*1.4:uD.rgb;   // light glyphs (Paper colour) on Ink background
    outc=mix(uC.rgb,fg,g);
  }
  fragColor=TDOutputSwizzle(vec4(mix(orig,outc,uB.w),1.));
}
