// Per-particle colour: gradient from Color (birth) to Colorend (death) over normalised age, speed brightening, fade in/out.
void main() {
	const uint id = TDIndex();
	if (id >= TDNumElements())
		return;
	float life = max(TDIn_PartLifeSpan(), 1e-4);
	float t = clamp(TDIn_PartAge() / life, 0.0, 1.0);
	float speed = length(TDIn_PartVel());
	vec3 c = mix(uColor.rgb, uColorEnd.rgb, smoothstep(0.0, 1.0, t));
	c *= 0.6 + 0.4 * clamp(speed * 0.35, 0.0, 2.0);
	float a = smoothstep(0.0, 0.05, t) * (1.0 - smoothstep(0.65, 1.0, t));
	Color[id] = vec4(c, a);
}
