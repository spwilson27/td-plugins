# POP_boids

3D flocking on the GPU. The points of the input POP become the flock: boid count = input point count (capped by `Maxboids`), start positions = the input `P`. With nothing connected a built-in demo scatter of points is used (gated Base COMP `demo`, not cooked when in1 is connected).

Positions and velocities live in two rgba32float feedback textures (side x side, side = ceil(sqrt(count))), seeded from the input points via POP to TOP. A GLSL TOP does a brute-force neighbour search over all boids (separation / alignment / cohesion, nearest periodic image when wrapping), clamps speed, handles box bounds (wrap or bounce) and an optional spherical obstacle. Results are converted with TOP to POP; a Copy POP stamps a tapered cone onto every boid, rotated along its heading.

**Inputs**: `in1` points (POP, optional, the flock). `in2` modulation CHOP (optional, last input): channels `band1`-`band4`, `beat`; missing channels are ignored. Used here: band1 scales Cohesion x(1+3b), beat scales Wander x(1+4b).

| Output | Content |
|---|---|
| out1 | boid points (POP): `P` position, `N` unit heading, `Color` (from speed and heading) |
| out2 | instanced cone mesh (POP), one cone per boid; render it with a Geometry COMP |

There is no render output. The node viewer shows an internal `preview` TOP (fixed orbit camera, uses absTime, preview only).

| Page | Param | Notes |
|---|---|---|
| Controls | Play, Reset, Seed | Reset re-seeds positions from the input points (also happens when the flock size changes); Seed randomizes initial velocities |
| | Maxboids | cap on the flock (8192 default). The neighbour pass is O(N^2): 16384 costs roughly 27 ms/frame on the dev machine, so keep large inputs capped (only the first Maxboids points flock) |
| | Speed | simulation time scale |
| Flocking | Separation, Alignment, Cohesion | steering weights |
| | Sepradius, Aliradius, Cohradius | neighbour radii (world units) |
| | Maxspeed, Minspeed, Maxforce, Wander | speed limits, steering limit, random turning |
| Bounds | Boundsize | half extent of the cubic box (input points outside it are wrapped/clamped) |
| | Boundmode | wrap (torus) or bounce |
| | Obstacle, Obstaclepos, Obstacleradius | spherical obstacle boids steer around (drawn in the preview only) |
| Look | Boidsize, Color1, Color2 | cone size; slow/fast colours (also tinted by heading) |

Snippets: `snippets/POP_boids.tox` (About > Snippets). Renamed from `GEN_boids`.
