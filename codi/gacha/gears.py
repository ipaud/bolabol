"""Involute spur gear outlines and face-gear (crown) tooth sections. Pure math, mm."""
from math import pi, sin, cos, tan, acos, radians


def inv(a):
    return tan(a) - a


def polar(r, a):
    return r * cos(a), r * sin(a)


def spur_profile(m, z, pa_deg, backlash=0.0, phase_deg=0.0, n_flank=8, n_arc=3):
    """Closed polygon of an involute spur gear centred at the origin.
    Tooth 0 is centred at polar angle phase_deg (CCW from +X). Teeth are thinned by backlash/2."""
    a = radians(pa_deg)
    r = m * z / 2.0
    rb, ra, rf = r * cos(a), r + m, r - 1.25 * m
    psi_p = (pi * m / 2.0 - backlash / 2.0) / (2.0 * r)

    def psi(R):
        return psi_p + inv(a) - inv(acos(min(1.0, rb / R)))

    if psi(ra) <= 0:
        raise ValueError("pointed teeth: z=%d m=%.2f" % (z, m))
    r0 = max(rb, rf)
    Rs = [r0 + (ra - r0) * i / (n_flank - 1) for i in range(n_flank)]
    step, ph = 2 * pi / z, radians(phase_deg)
    pts = []
    for k in range(z):
        c = ph + k * step
        if rf < rb:
            pts.append(polar(rf, c - psi(rb)))
        pts += [polar(R, c - psi(R)) for R in Rs]
        t0, t1 = c - psi(ra), c + psi(ra)
        pts += [polar(ra, t0 + (t1 - t0) * i / n_arc) for i in range(1, n_arc)]
        pts += [polar(R, c + psi(R)) for R in reversed(Rs)]
        if rf < rb:
            pts.append(polar(rf, c + psi(rb)))
        u0, u1 = c + psi(rb), c + step - psi(rb)
        pts += [polar(rf, u0 + (u1 - u0) * i / n_arc) for i in range(1, n_arc)]
    return pts


def crown_section(r, m, z_c, z_p, pa_deg, z_pin_axis, z_root, backlash=0.0):
    """Face gear tooth cross-section at radius r (teeth hang down from z_root).

    A spur pinion (base radius rb) meshes at radius r like a straight rack with pressure angle
    alpha(r) = acos(r0*cos(pa)/r), rolling on its circle r_p*r/r0. Returns
    (half_width_at_tip, half_width_at_root, z_tip, alpha) with widths along the tangent (arc length).
    """
    a0 = radians(pa_deg)
    r0, rp = m * z_c / 2.0, m * z_p / 2.0
    alpha = acos(r0 * cos(a0) / r)
    rpp = rp * r / r0
    s_pin = 2.0 * rpp * (pi / (2.0 * z_p) + inv(a0) - inv(alpha))   # pinion tooth at its rolling circle
    pitch = 2.0 * pi * r / z_c
    w_t = pitch - s_pin - backlash / 2.0                          # crown tooth at the pitch line
    z_line = z_pin_axis + rpp
    z_tip = z_root - 2.25 * m
    half_tip = w_t / 2.0 - (z_line - z_tip) * tan(alpha)
    half_root = w_t / 2.0 + (z_root - z_line) * tan(alpha)
    half_root = min(half_root, pitch / 2.0 - 0.05)
    return half_tip, half_root, z_tip, alpha
