uniform vec4 uT;   // x = fade, y = play
out vec4 fragColor;
void main(){
    vec4 p = texture(sTD2DInputs[0], vUV.st);
    vec4 r = texture(sTD2DInputs[1], vUV.st);
    fragColor = TDOutputSwizzle(uT.y > 0.5 ? p*uT.x + r : p);
}
