// SDF_from_POP / mesh: the volume bounds as a 2x1 texture (texel 0 = min xyz, texel 1 = max xyz), from vox's bnd buffer
out vec4 fragColor;
void main(){
    int o = int(gl_FragCoord.x) * 3;
    fragColor = vec4(TDBuffer_vbnd(0, o), TDBuffer_vbnd(0, o + 1), TDBuffer_vbnd(0, o + 2), 0.0);
}
