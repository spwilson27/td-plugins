// glyph atlas: 10 single-glyph Text TOPs laid out left to right (inputs 0..9)
out vec4 fragColor;
void main(){
  vec2 uv=vUV.st; float x=uv.x*10.; int i=int(floor(x)); vec2 l=vec2(fract(x),uv.y);
  float v=0.;
  switch(i){
    case 0: v=texture(sTD2DInputs[0],l).r; break;
    case 1: v=texture(sTD2DInputs[1],l).r; break;
    case 2: v=texture(sTD2DInputs[2],l).r; break;
    case 3: v=texture(sTD2DInputs[3],l).r; break;
    case 4: v=texture(sTD2DInputs[4],l).r; break;
    case 5: v=texture(sTD2DInputs[5],l).r; break;
    case 6: v=texture(sTD2DInputs[6],l).r; break;
    case 7: v=texture(sTD2DInputs[7],l).r; break;
    case 8: v=texture(sTD2DInputs[8],l).r; break;
    default: v=texture(sTD2DInputs[9],l).r; break;
  }
  fragColor=TDOutputSwizzle(vec4(vec3(v),1.));
}
