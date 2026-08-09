# Orbital Mechanics & Orbit Determination, From Scratch

A from-zero primer for Ariadne. Every number below is computed,
not guessed; you can rerun the Python snippets yourself.

---

## 0. Acronym glossary (full forms)

| Acronym | Full form |
|---|---|
| TLE | Two-Line Element (set), the standard text format for describing a satellite's orbit |
| NORAD | North American Aerospace Defense Command, the body that catalogs tracked space objects |
| SGP4 | Simplified General Perturbations model, version 4 |
| ECI | Earth-Centered Inertial (reference frame) |
| ECEF | Earth-Centered, Earth-Fixed (reference frame) |
| TEME | True Equator, Mean Equinox (the reference frame SGP4 natively outputs in) |
| RAAN | Right Ascension of the Ascending Node |
| BSTAR | "B-star", a drag term used in the SGP4 model (not a literal acronym, just notation) |
| J2 | The 2nd zonal harmonic, the dominant term describing Earth's equatorial bulge |
| GM / μ | Standard gravitational parameter (G = gravitational constant, M = mass of Earth) |
| KF | Kalman Filter |
| EKF | Extended Kalman Filter |
| UKF | Unscented Kalman Filter |
| OD | Orbit Determination |
| NEES | Normalized Estimation Error Squared |
| NIS | Normalized Innovation Squared |
| RIC | Radial, In-track, Cross-track (a relative reference frame) |
| TCA | Time of Closest Approach |
| Pc | Probability of collision |
| HBR | Hard-Body Radius (combined physical size of two objects, for collision-risk purposes) |
| CZML | Cesium Markup Language (a JSON-based format Cesium uses for time-dynamic 3D scenes) |
| LEO | Low Earth Orbit (roughly 160 km–2000 km altitude) |
| API | Application Programming Interface |
| REST | Representational State Transfer (a style of API over HTTP) |
| CLI | Command-Line Interface |
| RK4 / RK45 | Runge-Kutta 4th order / adaptive 4th-5th order (numerical integration methods) |
| CORS | Cross-Origin Resource Sharing (browser security rule for cross-domain API calls) |
| UTC | Coordinated Universal Time |

---

## 1. What an orbit actually is

A satellite in orbit is in continuous free-fall around Earth.
Gravity provides the centripetal force. For a circular orbit of radius `r`:

```
G*M*m / r²  =  m*v² / r
```

Cancel `m`, solve for `v`:

```
v = sqrt(G*M / r)
```

Real satellite orbits are ellipses, not circles (Kepler's 1st law, Earth sits at one focus).
Kepler's 2nd law (equal areas in equal times) and 3rd law (`T² ∝ a³`) are also both direct
consequences of the same inverse-square gravity, just derived via angular momentum
conservation and energy conservation instead of the simple circular case.

Define the **standard gravitational parameter**:

```
μ = G * M_earth = 398,600.4418 km³/s²
```

This single constant (`μ`) is what shows up everywhere below instead of `G` and `M`
separately, it's known far more precisely than `G` and `M` individually.

**Kepler's third law, precisely, for an ellipse of semi-major axis `a`:**

```
T = 2π * sqrt(a³ / μ)
```

---

## 2. The six numbers that describe *any* orbit (Keplerian elements)

A circle needs 1 number (radius) to describe it. An ellipse in 3D space, at a specific
orientation, needs **6** numbers, these are the *Keplerian orbital elements*:

1. **`a`**, semi-major axis (size of the ellipse, km)
2. **`e`**, eccentricity (shape: 0 = circle, closer to 1 = more elongated)
3. **`i`**, inclination (tilt of the orbital plane vs. Earth's equator, degrees)
4. **`RAAN` (Ω)**, Right Ascension of the Ascending Node (where the orbit crosses the
   equator going north, measured against a fixed direction in space, the vernal equinox)
5. **`ω`**, argument of perigee (where along the ellipse the closest point to Earth is,
   measured from the ascending node)
6. **`ν` or `M`**, true anomaly or mean anomaly (where the satellite *currently* is along
   its orbit, this is the one number that changes fastest, second by second)

(1) and (2) define the ellipse's size and shape. (3) and (4) define which plane in 3D space
it sits in. (5) defines the ellipse's orientation *within* that plane. (6) is a clock
position. This is exactly what the "Orbit Parameters" panel in your dashboard mockup shows.

---

## 3. TLE format, decoding real numbers

A TLE (Two-Line Element set) is how NORAD publishes an orbit as compact plain text. Example,
in the standard format (illustrative, TLEs are re-issued daily, so treat the numbers as a
snapshot for teaching, not live data):

```text
1 25544U 98067A   24045.51782528  .00016717  00000-0  10270-3 0  9998
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49560684436460
```

**Line 1** decodes as:

| Field | Value | Meaning |
|---|---|---|
| Catalog number | 25544 | NORAD ID |
| Classification | U | Unclassified |
| Intl designator | 98067A | Launched 1998, 67th launch of the year, piece A |
| Epoch | 24045.51782528 | Year 2024, day 45.51782528 of the year (fractional day = time of day) |
| Mean motion drift (n_dot/2) | 0.00016717 | drag-related, first derivative of mean motion |
| BSTAR | 10270-3 → 0.10270×10⁻³ | drag coefficient term used inside SGP4 |

**Line 2** decodes as (these are the 6 Keplerian elements, in TLE's own order):

| Field | Value |
|---|---|
| Inclination `i` | 51.6416° |
| RAAN `Ω` | 247.4627° |
| Eccentricity `e` | 0.0006703 (decimal point is implied, TLEs never write it) |
| Argument of perigee `ω` | 130.5360° |
| Mean anomaly `M` | 325.0288° |
| Mean motion `n` | 15.49560684 revolutions/day |

Note eccentricity here is tiny (0.00067), this is a near-circular LEO orbit, typical of the
ISS. An eccentricity of 0.5 would be a visibly stretched ellipse; Earth-crossing comets can
approach `e ≈ 0.99`.

### Turning mean motion into semi-major axis

Mean motion is given in rev/day. Convert to rad/s, then invert Kepler's third law:

```
n = 15.49560684 rev/day × (2π rad/rev) / (86400 s/day)
  = 1.12687233 × 10⁻³ rad/s

a = (μ / n²)^(1/3)
  = (398600.4418 / (1.12687233e-3)²)^(1/3)
  = 6796.147 km
```

Earth's equatorial radius is `Re = 6378.137 km`, so:

```
altitude = a - Re = 6796.147 - 6378.137 = 418.01 km
```

That's a realistic ISS altitude. And the period:

```
T = 2π * sqrt(a³/μ) = 5575.77 s = 92.93 minutes
```

That matches the ISS's well-known ~93-minute orbit. **This is exactly what
`ariadne/models/tle.py` and `ariadne/propagate/sgp4.py` need to compute** (SGP4 does this
plus a lot more, see §5).

### Speed at perigee vs. apogee (vis-viva equation)

The **vis-viva equation** gives speed anywhere on the ellipse:

```
v = sqrt(μ * (2/r - 1/a))
```

At perigee (`r_p = a(1-e) = 6791.59 km`): `v_p = 7.6635 km/s`
At apogee (`r_a = a(1+e) = 6800.70 km`): `v_a = 7.6533 km/s`

Almost identical here because `e` is tiny (nearly circular). For a highly eccentric orbit
the difference would be dramatic, this is the same physics as a pendulum swinging faster at
the bottom.

---

## 4. Reference frames, why so many, and what each one is for

A position "in space" is meaningless without saying *relative to what*. Ariadne needs four:

- **TEME** (True Equator, Mean Equinox), what SGP4 natively outputs. A quirky,
  SGP4-specific frame, not directly usable for anything else.
- **ECI** (Earth-Centered Inertial), a frame fixed relative to the distant stars, not
  rotating with Earth. Good for propagation/dynamics because Newton's laws are simplest in
  an inertial (non-accelerating, non-rotating) frame. Going TEME → ECI corrects for
  precession/nutation (Earth's axis wobbles slowly, like a spinning top).
- **ECEF** (Earth-Centered, Earth-Fixed), rotates *with* Earth. A ground station has a
  fixed position in this frame. Going ECI → ECEF just requires rotating by Earth's current
  sidereal rotation angle (Earth spins ~360.986°/day, very slightly more than 360°, because
  Earth also moves along its orbit around the Sun in that day).
- **Topocentric** (azimuth/elevation/range), centered on a specific ground observer, telling
  you "look this compass direction, this angle above the horizon, this far away." This is
  what a telescope or radar dish actually points at.

The chain is always: **TEME → ECI → ECEF → topocentric**, each step a rotation matrix
(sometimes plus a small correction). This is `ariadne/propagate/frames.py`.

---

## 5. SGP4, what problem it actually solves

You might think: "I have position and velocity, why not just numerically integrate Newton's
law forward in time?" You can (that's `ariadne/propagate/numerical.py`, using RK4/RK45), but
it's slow if you need to propagate thousands of catalog objects repeatedly, and real orbits
aren't pure two-body, Earth's oblateness (J2), atmospheric drag, and other objects all perturb
it.

SGP4 (Simplified General Perturbations model, version 4) is a **closed-form analytic model**:
someone did the perturbation math once (this is genuinely serious 1970s-80s aerospace
mathematics, mostly Kozai/Brouwer/Vallado), producing equations you can evaluate directly for
position/velocity at any future time, without step-by-step integration. It bakes in:

- Secular (steadily accumulating) drift from J2 in RAAN and argument of perigee
- Periodic wobbles at orbital-period timescale
- A drag model driven by the BSTAR term from the TLE

The catch: SGP4 only works correctly with TLE-derived "mean elements", you cannot feed it
elements from another source and expect correct results. This is why `ariadne/models/tle.py`
(TLE parsing) has to come before `ariadne/propagate/sgp4.py` (the actual propagator) in the
build order.

---

## 6. The estimation problem, why we need a filter at all

Suppose you have a radar that measures range and angle to a satellite. Every measurement has
noise. If you just used the raw measurement as "the" position, your estimate would jump
around noisily and you'd have no idea how much to trust it.

The fix is **recursive Bayesian estimation**: maintain a running belief about the state
(position + velocity), expressed as a mean `x̂` and a covariance matrix `P` (how uncertain you
are, and how the uncertainty in different variables is correlated). Every time step:

1. **Predict**, propagate `x̂` forward using the dynamics model (orbital motion), and grow
   `P` accordingly (uncertainty increases between measurements).
2. **Update**, when a new measurement arrives, blend it with your prediction, weighted by
   how much you trust each source. Uncertainty `P` shrinks.

This predict/update loop *is* the Kalman filter family. The only question is how to handle
the fact that orbital dynamics and the range/angle measurement model are **nonlinear**.

---

## 7. The Unscented Kalman Filter (what `ukf.py` implements)

**The problem with a plain (linear) Kalman filter or EKF:** propagating a Gaussian
probability distribution through a nonlinear function doesn't generally give you a Gaussian
back. The EKF handles this by linearizing (first-order Taylor expansion, i.e. computing a
Jacobian matrix) around the current estimate, but that throws away curvature information,
and for orbital dynamics over longer prediction gaps, that error compounds.

**The UKF's trick:** instead of linearizing the function, pick a small, deterministic set of
sample points ("sigma points") that exactly capture the mean and covariance of your current
Gaussian belief, push *those* through the real, unmodified nonlinear function, then
reconstruct a new Gaussian from the transformed points. No Jacobians needed anywhere.

### Sigma points

For an `n`-dimensional state, you use `2n + 1` sigma points:

```
χ0    = x̂
χi    = x̂ + ( sqrt((n+λ) * P) )_i        for i = 1..n
χi    = x̂ - ( sqrt((n+λ) * P) )_(i-n)    for i = n+1..2n
```

`sqrt((n+λ)*P)` means a matrix square root (Cholesky decomposition) of `(n+λ)P`, and
`(...)_i` means "the i-th column of that matrix." `λ` is a scaling parameter:

```
λ = α² * (n + κ) − n
```

`α` controls how spread out the sigma points are (typically tiny, like `1e-3`, to stay in the
region where the nonlinear function is well-behaved), `β` encodes prior knowledge about the
distribution's shape (`β = 2` is optimal for Gaussians), and `κ` is a secondary scaling
parameter (often `0`).

**Worked example (n=6 state: 3 position + 3 velocity components):**

Using clean illustrative values `α=1, β=2, κ=3−n=−3` (a standard textbook choice for
5 non-degenerate weights before switching to the tiny-α convention used in practice):

```
λ = 1² * (6 + (-3)) - 6 = 3 - 6 = -3
n + λ = 3
sqrt(n+λ) = 1.732
Wm0 = λ/(n+λ)              = -3/3        = -1.0
Wc0 = λ/(n+λ) + (1-α²+β)   = -1.0 + 2    =  1.0
Wi  = 1/(2(n+λ))           = 1/6         =  0.1667   (for all 12 remaining points)
check: Wm0 + 12*Wi = -1.0 + 2.0 = 1.0   ✓ (weights must sum to 1)
```

Note `Wm0` is *negative*, that's allowed and expected; these aren't probabilities, they're
just weights in a weighted average.

In practice (and in `ariadne/estimate/ukf.py`), you'd instead use `α = 1e-3, κ = 0`, which
gives `λ = -5.999994`, `n+λ ≈ 6×10⁻⁶`, and `sqrt(n+λ) ≈ 0.00245`, the sigma points sit
extremely close to `x̂`, which keeps the linearization region tight and numerically stable for
a nonlinear, sensitive system like orbital dynamics.

### Predict and update

**Predict:** push each sigma point through the nonlinear dynamics function `f` (numerical
propagation, or SGP4-like physics), then recombine:

```
χ'i = f(χi)
x̂'  = Σ Wm_i * χ'i
P'  = Σ Wc_i * (χ'i - x̂')(χ'i - x̂')ᵀ  + Q      (Q = process noise, from noise_models.py)
```

**Update:** push the *predicted* sigma points through the nonlinear measurement function `h`
(e.g., range/azimuth/elevation from a ground station), then compute the Kalman gain and
correct:

```
Zi = h(χ'i)
ẑ  = Σ Wm_i * Zi
S  = Σ Wc_i * (Zi - ẑ)(Zi - ẑ)ᵀ + R              (R = measurement noise)
Pxz = Σ Wc_i * (χ'i - x̂')(Zi - ẑ)ᵀ
K  = Pxz * S⁻¹                                    (Kalman gain)
x̂  = x̂' + K * (z_actual - ẑ)                      (z_actual - ẑ is the "innovation")
P  = P' - K * S * Kᵀ
```

This is exactly the structure in `ariadne/estimate/ukf.py`. `ariadne/estimate/dynamics.py`
supplies `f`, `ariadne/estimate/noise_models.py` supplies `Q` and `R`.

---

## 8. NEES and NIS, checking whether you can trust `P`

A filter can produce an estimate that's close to truth while reporting a `P` matrix that's
wildly wrong (overconfident or underconfident). NEES and NIS check this.

**NEES** (Normalized Estimation Error Squared), requires knowing ground truth, so it's used
in simulation/testing, not live operation:

```
NEES = (x_true - x̂)ᵀ * P⁻¹ * (x_true - x̂)
```

If `P` is correct, NEES follows a **chi-squared distribution with `n` degrees of freedom**
(`n` = state dimension), and its expected value is exactly `n`. For `n=6` (3 position + 3
velocity), computed from the chi-squared distribution:

```
E[NEES] = 6
95% two-sided bounds: chi²(0.025, df=6) = 1.237   chi²(0.975, df=6) = 14.449
```

So if you run many trials and your average NEES sits at, say, 40, your filter is badly
**overconfident** (`P` too small, it's claiming more precision than it has). If it averages
0.3, it's **underconfident** (`P` too large, overly conservative).

**NIS** (Normalized Innovation Squared), uses the measurement residual instead, so it needs
no ground truth and *can* run in live operation:

```
NIS = (z_actual - ẑ)ᵀ * S⁻¹ * (z_actual - ẑ)
```

For a 3-dimensional measurement (range, azimuth, elevation), `m=3`:

```
E[NIS] = 3
95% two-sided bounds: chi²(0.025, df=3) = 0.216   chi²(0.975, df=3) = 9.348
```

This is what `ariadne/estimate/diagnostics.py` computes and checks against.

---

## 9. Conjunction assessment, the math behind "Next Close Approach"

### 9.1 Relative state and TCA (Time of Closest Approach)

Given two propagated objects, define the relative position vector at any time `t`:

```
r_rel(t) = r_2(t) - r_1(t)
```

TCA is the time that minimizes `|r_rel(t)|`. Calculus says: minimize `|r_rel(t)|²` instead
(avoids the square root), and set its derivative to zero:

```
d/dt [ r_rel(t) · r_rel(t) ] = 2 * r_rel(t) · v_rel(t) = 0
```

So TCA is where the relative position and relative velocity vectors are **perpendicular**, which
makes physical sense: that's the instant the range stops decreasing and starts increasing.
Because the two trajectories are each nonlinear (from SGP4/orbital dynamics), this equation
generally has no closed-form solution, `ariadne/conjunction/tca.py` solves it numerically
(golden-section or Brent's method: bracket the root, narrow it down).

### 9.2 RIC frame

Once you have the relative state at TCA, rotate it into the **RIC frame**
(Radial / In-track / Cross-track), defined relative to the *primary* object's own orbit:

- **R** (radial): points from Earth's center through the primary object
- **I** (in-track): points along the primary's velocity direction (perpendicular to R,
  in the orbital plane)
- **C** (cross-track): completes the right-handed set, perpendicular to the orbital plane

```
R̂ = r_1 / |r_1|
Ĉ = (r_1 × v_1) / |r_1 × v_1|
Î = Ĉ × R̂
```

Why bother? Because collision risk is **anisotropic** in this frame, for a typical LEO
encounter, uncertainty along the in-track direction (essentially: timing/along-orbit error)
is usually much larger than radial or cross-track uncertainty, so expressing everything in
RIC makes covariance combination and the encounter-plane projection (next section) tractable.

### 9.3 Probability of collision (Pc)

At TCA, project both objects' position covariances onto the 2D plane perpendicular to the
relative velocity vector (the "encounter plane"), combine them (`C = C1 + C2`, since the two
objects' errors are independent), and integrate a 2D Gaussian, centered at the miss vector,
over a disk of radius equal to the combined **hard-body radius** (HBR, the sum of both
objects' physical radii, since if their *centers* pass within that combined distance, they
physically collide):

```
Pc = ∬_{disk of radius HBR}  (1 / (2π * sqrt(det C)))  *  exp( -0.5 * (r - d)ᵀ C⁻¹ (r - d) )  dr
```

where `d` is the miss-distance vector in the encounter plane. This is the Foster/Alfano-style
formulation, `ariadne/conjunction/probability.py`'s job. In general it's evaluated
numerically (no clean closed form), but there's a useful **leading-order approximation** when
the HBR is small compared to the position uncertainty `σ` (assuming a roughly circular,
isotropic covariance in the encounter plane with `σx ≈ σy ≈ σ`):

```
Pc ≈ (HBR² / (2σ²)) * exp( -d² / (2σ²) )
```

**Worked example, matched to your dashboard mockup** (miss distance `d = 2.45 km`, displayed
`Pc = 1.23×10⁻⁴`):

Solving the approximation backward: for a *fixed* miss distance `d`, this expression is
maximized (worst case) exactly when `σ = d/√2`:

```
σ* = 2450 m / √2 = 1732.4 m
```

That is, an encounter-plane position uncertainty of about 1.7 km per axis. Interesting and
slightly counterintuitive result: **Pc is not monotonic in uncertainty.** Too little
uncertainty (very confident tracking) and the tight Gaussian mostly misses the disk
entirely, low Pc. Too much uncertainty and the Gaussian is smeared so thin across a huge
area that the probability mass landing on the small disk is again low. Risk peaks at an
*intermediate* uncertainty. This is a real, well-known effect in the conjunction-assessment
field (a small Pc doesn't always mean "safe", it can mean "we don't know well enough to
say, " which is exactly why NEES/NIS validation upstream matters: a badly-calibrated
covariance silently distorts every Pc downstream).

At that worst-case `σ`, solving for the combined hard-body radius that reproduces the
mockup's displayed `Pc = 1.23×10⁻⁴`:

```
HBR = sqrt( Pc * d² * e )  =  sqrt( 1.23e-4 * 2450² * 2.71828 )  ≈  44.8 m
```

That's a large combined HBR (consistent with the mockup's object being a rocket-body upper
stage, "BREEZE-M R/B", these can be several meters across, and a conservative combined
HBR against another sizeable object can reasonably land in the tens-of-meters range).

---

## 10. How it all connects to the dashboard

| Dashboard element | Comes from |
|---|---|
| Orbit Parameters panel | §2/§3, Keplerian elements, decoded from TLE via `models/tle.py` |
| Object position on the 3D globe | §5, SGP4 propagation → §4 frame transforms → CZML |
| Next Close Approach panel | §9, `tca.py`, `ric.py`, `probability.py` |
| Trustworthiness of the Pc number | §8, NEES/NIS validating the UKF's `P` that feeds Pc |
| "1247 Objects Tracked" | `fetch/celestrak.py` catalog pull |
| Live globe animation | `export/czml.py` output, consumed by CesiumJS in the frontend |

Every number on that mockup traces back to one of the formulas above, none of it is
decorative. The build plan in `CLAUDE.md` fills these in, in the dependency order shown here:
propagation before conjunction, estimation covariance before Pc, all of it before export.
