"""Gachapon (compact Bandai Capsule Station layout) - master dimensions in millimetres.

Frame: X right, Y back (machine front faces -Y), Z up. Rotor axis at X=Y=0, floor at Z=0.
Blender units are metres (physics needs real scale); builders convert with MM.
Front-view angles (parts turning about Y) are measured clockwise from +Z, as seen from the front.
"""
from math import radians, degrees, pi, sin, cos, tan, asin, acos, sqrt

MM = 0.001
STYLE = "v1"                # shell: "v1" square / "mochi" rounded v2 (set by build.main(style=...))

# ---- printing / fits (FDM 0.4 nozzle, PETG) ----
BED = 220.0                 # square bed of the user's printer
BED_MARGIN = 3.0
CLR_SLIDE = 0.30            # diametral, pin/shaft sliding in bore
CLR_FREE = 0.40             # diametral, free running
GEAR_BACKLASH = 0.40        # total per mesh, split half per gear (FDM: 0.2-0.4 recommended)

# ---- capsule: two-piece, clear top = outer sleeve, coloured bottom = inner spigot ----
CAP_R = 25.0
CAP_BAND = 4.0              # cylinder band at the seam -> 50 x 54 capsule
CAP_H = 2 * CAP_R + CAP_BAND
CAP_WALL = 1.2
CAP_GAP = 0.20              # radial sliding gap sleeve/spigot
CAP_OVERLAP = 7.0           # spigot engagement
CAP_BEAD_H = 0.35           # radial bead -> 0.15 mm snap interference
CAP_BEAD_W = 1.4
CAP_BEAD_Z = 1.15           # bead centre above the seam (inside the cylinder band)
CAP_SEAM = 0.05             # gap between sleeve rim and spigot shoulder when closed
CAP_BEAD_SEGS = 4
CAP_BEAD_ARC = 40.0         # deg per bead segment
CAP_MASS = 0.015            # kg, shell + toy

# ---- rotor: 5 pockets, crown gear underneath (Bandai JP3267512B2 layout) ----
N_POCKETS = 5
POCKET_D = 58.0
R_POCKET = 56.5
ROT_T = 28.0
ROT_R = 101.5
ROT_GAP = 1.0               # rotor underside above deck top
CS_DEPTH = 16.0             # countersink over every pocket (mouth r 42.4: 2.6 mm land at the rim, 4 mm at the hub)
CS_SLOPE = 50.0             # was 35/12 (mouth r 46): two capsules bridged on the shallow cone and the pocket came
                            # round empty in 6 % of turns (clean continuous Bullet test, 18 seeds); 50/16: 0/144
EXIT_ANGLE = 150.0          # deg CCW from +X (back-left): pocket parked over the drop hole
EXIT_HOLE_D = 60.0
HUB_CONE_R0 = 10.0
HUB_CONE_R1 = 4.0
HUB_CONE_H = 24.0
RING_T = 3.0                # crown ring flange, sits in a recess under the rotor
RING_R0 = 87.0
RING_PRESS = 0.1            # radial interference ring bore / rotor boss: the ring hangs under the rotor and
                            # used to drop 1 mm onto the deck (teeth jam from -0.4 mm); + a drop of CA per tab
RAIL_GAP = 0.2              # deck rail under the crown ring flange (outside the teeth), 1 layer below the ring:
                            # caps the rotor tilt at the mesh (0.25 deg towards the pinion already jams)
PIVOT_D = 12.0              # printed pivot post on the deck
SHIM_NOM = 0.4              # rotor sits on a 0.4 mm shim: swap 0.2/0.6 to tune the crown/pinion mesh

# ---- face gear: crown on rotor underside + spur pinion (25 deg for strength) ----
GM = 2.0
PA_CROWN = 25.0
Z_PIN = 19
Z_CROWN = N_POCKETS * Z_PIN  # 95 -> one handle turn = one pocket = 72 deg
CROWN_R_IN = 88.0            # > interference limit 87.2
CROWN_R_OUT = 98.0           # keeps the crown top land >= 0.8 mm with 0.4 backlash
PIN_Y0 = CROWN_R_IN - 0.25
PIN_Y1 = CROWN_R_OUT + 0.25

# ---- gear column: A on handle shaft (low), B coupled to the pinion (high), 1:1 ----
Z_COL = 18
PA_COL = 20.0
COL_Y0, COL_Y1 = 72.0, 84.0   # 12 mm faces (was 8: 34 MPa at 100 N on the crank, no margin); grown forward
BRACKET_Y = (66.5, 70.5)    # front support of the pinion axle, screwed under the deck
BRACKET_SCREWS = ((-7.0, 63.0), (7.0, 63.0))

# ---- vertical levels ----
Z_DECK = 205.0                              # deck disk top: capsules slide here
Z_ROT_BOT = Z_DECK + ROT_GAP                # 206
Z_ROT_TOP = Z_ROT_BOT + ROT_T               # 234
Z_CROWN_PITCH = Z_ROT_BOT - 1.25 * GM       # 203.5
Z_CROWN_TIP = Z_ROT_BOT - 2.25 * GM         # 201.5
Z_PIN_AX = Z_CROWN_PITCH - GM * Z_PIN / 2   # 184.5
Z_HANDLE = Z_PIN_AX - GM * Z_COL            # 148.5
DECK_DISK_R = 84.0          # was 86: the r 86.5 drop hole left a 0.4 mm crescent; no capsule rests past r 84
Z_DECK_PLATE_TOP = Z_CROWN_TIP - 2.5        # 199
DECK_PLATE_T = 4.0

# ---- body ----
WALL = 3.2
XI = ROT_R + 2.0            # interior half width 103.5
YF = -105.0                 # front interior face
YR = ROT_R + 1.0            # rear interior face 102.5 (exterior depth 213.9 fits the bed)
XO, YFO, YRO = XI + WALL, YF - WALL, YR + WALL
Z_FLOOR_T = 3.2
Z_SPLIT = 117.0             # base box / mech box joint
Z_BODY_TOP = 230.0
FUNNEL_R = ROT_R + 1.0
Z_FUNNEL_LIP = Z_ROT_TOP + 0.5
FUNNEL_SLOPE = 35.0
Z_RIM = 236.0               # funnel rim top = case bottom
Z_CASE_TOP = 404.0
LID_T = 6.0
LEDGE = 3.0                 # deck ledge width on walls

# ---- token mechanism: the printed token is the key (classic handle-integrated coin mech) ----
# The knob carries a radial slit at 12 o'clock. At home the blocking pawl rests inside the empty
# slit, so the handle cannot turn; a token pushed in flush lifts the pawl (45 deg lead-in).
# At 6 o'clock the token drops through the bezel into a chute that feeds the drawer.
TOKEN_D = 25.0
TOKEN_T = 4.0
KNOB_R = 46.0
KNOB_Y0 = YFO - 1.8                         # knob back face (-111)
KNOB_Y1 = KNOB_Y0 - 30.0                    # knob front face (-141)
TOKEN_PROUD = 0.2
SLIT_W = TOKEN_T + 0.6
SLIT_FLOOR_R = KNOB_R + TOKEN_PROUD - TOKEN_D   # 21.2
SLIT_Y_REAR = KNOB_Y1 + TOKEN_D + 1.0           # -115
SLIT_SLOPE = 2.0            # floor falls towards the back: the token self-seats on the rear stop
TOKEN_Y = SLIT_Y_REAR - TOKEN_D / 2 - 0.3      # -127.8 token centre when seated
GRIP_W, GRIP_H, GRIP_D = 80.0, 14.0, 12.0
BEZEL_R0, BEZEL_R1 = KNOB_R + 1.0, KNOB_R + 14.0
DOG_LEVER = 17.0            # nose -> pivot along the tangent
DOG_OFFSET = 8.0            # pivot outboard of the tangent line (self-locking, lever clears rim)
DOG_NOSE_H = 5.0            # nose height below the lever
DOG_TIP = (-2.0, 0.0)       # nose tip x-span at home; slit spans +-SLIT_W/2
DOG_RAMP = 30.0             # deg, +x flank: cams the nose out when turning backwards
DOG_STOP = 9.5              # deg: a foot under the lever lands on the knob rim -> locked angle is fixed
DOG_Y0, DOG_Y1 = TOKEN_Y - 9.7, TOKEN_Y + 3.3   # 6 mm lead-in chamfer in front, flat over the token top
RAT_Y0 = YF + 0.8
RAT_Y1 = RAT_Y0 + 5.0
RAT_R = 30.0
RAT_DEPTH = 3.0
RAT_PITCH = 15.6            # deg (20 teeth over 312 deg)
RAT_PAWL_ANGLE = -25.0      # front-view deg
RAT_FREE = (-8.0, 40.0)     # handle angles without teeth: back-off zone around home
RAT_NOTCH = 1.0             # home detent depth
RAT_HOME_STEP = 0.0         # v3: > 0 = hard home stop (a ratchet face at RAT_FREE[0]) + ramp of this many deg
M3_CLR = 3.4
SPRING_X = 5.0              # pen-spring seat over the blocking pawl lever (front-view x)
SPRING_D = 6.0
TCHUTE_W = 5.2
TCHUTE_SLOPE = 31.0
TCHUTE_Z_FRONT = 57.0       # token chute floor at the knob front plane
TCHUTE_TOP = Z_HANDLE - BEZEL_R1 - 0.5
DRAWER_X = (-12.0, 58.0)
DRAWER_Z = (6.0, 30.0)
DRAWER_D = 150.0            # drawer depth (was 36: coins piled up into the duct from ~12 and spilled past ~25)
DRAWER_RAMP = 35.0          # deg, ramp under the coin duct: coins slide to the back (Bullet pour test: duct
                            # clear to ~21-36 coins, first coin out of the drawer at ~40-56)
DRAWER_LOCK_X = 53.0        # 2 x M3x12 countersunk through the drawer front (right end) into nuts in a post
DRAWER_LOCK_Z = (12.0, 24.0)    # behind it: the drawer no longer just pulls out

# ---- handle shaft (printed hex) ----
HEX_AF = 16.0
HEX_CLR = 0.30
SLEEVE_D = 22.0
AXLE_D = 10.0
Y_SHAFT0 = KNOB_Y0 - 22.0   # shaft front end inside the knob
Y_SHAFT1 = YRO

# ---- v3 hidden coin mech (build.main(mech="v3"), parts_coin) ----
# Same lock principle, moved inside: the coin goes through a slot in a flush front plate into a
# carrier wheel just behind the front wall, and the handle is a plain crank. Under the deck ledge
# there is no room for the blocking pawl at 12 o'clock, so it waits DOG_ANGLE ahead of the pocket:
# an empty pocket catches it there (inside the ratchet back-off zone, so the handle goes back
# home); a coin fills the pocket and the pawl rides over it. At 6 o'clock the coin drops into a
# funnel and a duct down to the drawer.
MECH = "v2"
DOG_ANGLE = 0.0                     # front-view deg CW of the blocking pawl (v2: 12 o'clock)
DOG_LEAD = 0.0                      # 45 deg chamfer on the pawl nose's incoming (lock) flank tip
W_R = 38.0                          # coin wheel radius
W_Y0 = YF + 0.6                     # wheel front face, 0.6 behind the front wall
W_Y_STOP = W_Y0 + TOKEN_D + 1.5     # pocket rear stop
W_RAT_Y0 = W_Y_STOP + 2.5           # saw-tooth band (anti-reverse) behind the coin section
W_Y1 = W_RAT_Y0 + 6.0               # wheel rear face
PLATE_T = 3.0
PLATE_Y = YFO - PLATE_T             # coin plate front face
CRANK_Y0 = PLATE_Y - 1.0            # crank back face (flat, 1 mm off the plate), on the wheel boss
CRANK_Y1 = CRANK_Y0 - 15.0          # wing front face; the hub cap stands 2.5 mm proud of it
V3_TOP = Z_DECK_PLATE_TOP - DECK_PLATE_T - 3.5 - 0.7   # 0.7 under the deck ledge


def apply_mech(mech="v2"):
    """Switch the token path. "v3" redefines the shared token / pawl / ratchet constants for the
    coin wheel; build.main reloads the part modules afterwards so their `from params import *`
    copies see the new values."""
    g = globals()
    g["MECH"] = mech
    if mech != "v3":
        return
    token_y = W_Y_STOP - TOKEN_D / 2 - 0.3
    # the coin now reaches the pawl sideways: flush with the rim (a proud edge hit the steep lock flank
    # in the dynamic test and jammed the wheel) and a lead-in chamfer on that flank's tip, so a coin
    # up to DOG_LEAD proud or sunk cams the pawl up, while an empty pocket (2.5 mm drop) still locks
    g.update(KNOB_R=W_R, TOKEN_PROUD=0.0, SLIT_FLOOR_R=W_R - TOKEN_D, SLIT_Y_REAR=W_Y_STOP, TOKEN_Y=token_y,
             DOG_LEAD=0.8,
             DOG_Y0=token_y - 6.5, DOG_Y1=token_y + 6.5, DOG_ANGLE=50.0,
             BEZEL_R0=W_R + 1.0, BEZEL_R1=W_R + 14.0,
             RAT_R=W_R, RAT_Y0=W_RAT_Y0 + 0.5, RAT_Y1=W_RAT_Y0 + 5.5,
             # 18 teeth; back-off zone past the pawl stop. Home is a hard stop when backing off: a ratchet face 1.5
             # deg behind home (the 2 mm nose then rests at 0), then an 8 deg ramp. Before, the crank flopped from
             # -23.6 to +52 and the coin only enters with the wheel < 1-1.5 deg off home
             RAT_FREE=(-1.5, 360.0 - 18 * RAT_PITCH - 1.5), RAT_HOME_STEP=8.0,
             Y_SHAFT0=CRANK_Y0 - 11.5)

COIN_POCKETS = 1            # v3 coin wheel: 1 or 2 pockets side by side (2 = two coins per capsule; build.main(coins=2))
POCKET_PITCH = 8.0          # 2 pockets: centres +-4 mm (3.4 mm wall in the wheel, 2.4 mm between the plate slots).
                            # They pass under the same blocking pawl ~12 deg apart: an empty one catches it


def pocket_xs():
    return [0.0] if COIN_POCKETS == 1 else [-POCKET_PITCH / 2, POCKET_PITCH / 2]


RAT_SLEEVE_R = 3.2          # v3: housing sleeve through the anti-reverse pawl: the screw head clamps it, not the pawl

# ---- chute / outlet ----
CHUTE_W = 62.0
CHUTE_T = 2.4
Z_CUP = 12.0
CHUTE_SLOPE = 36.0         # steeper than 30: lying capsules slide, PETG friction margin
Y_CUP_BACK = -62.0
OUTLET_X = (-81.0, -17.0)
OUTLET_Z = (Z_CUP, 80.0)
CUP_LIP = 12.0


def exit_xy():
    a = radians(EXIT_ANGLE)
    return R_POCKET * cos(a), R_POCKET * sin(a)


def pocket_angle(k, turn_deg=0.0):
    """Rotor pocket k angle (deg CCW from +X) after the handle turned turn_deg clockwise."""
    return EXIT_ANGLE + k * 360.0 / N_POCKETS + turn_deg * Z_PIN / Z_CROWN


def fv(r, ang_deg):
    """Front-view point (x, z) at radius r, angle measured CW from +Z."""
    a = radians(ang_deg)
    return r * sin(a), r * cos(a)


def spin(x, z, deg):
    """Front-view point (x, z) turned deg clockwise about the handle axis."""
    a, zr = radians(deg), z - Z_HANDLE
    return x * cos(a) + zr * sin(a), Z_HANDLE - x * sin(a) + zr * cos(a)


def slit_floor(y):
    """Knob slit floor radius along Y (2 deg down towards the rear stop)."""
    return SLIT_FLOOR_R + (TOKEN_Y - y) * tan(radians(SLIT_SLOPE))


def tchute_floor(y):
    """Token chute floor height: falls towards the back (+Y) into the drawer."""
    return TCHUTE_Z_FRONT - (y - KNOB_Y1) * tan(radians(TCHUTE_SLOPE))


CUP_DROP = 4.6              # cup floor falls 6 deg towards the lip so the capsule rolls forward


def chute_floor(y):
    """Capsule path floor: 30 deg duct down to the cup, then a 6 deg cup floor down to the lip."""
    if y >= Y_CUP_BACK:
        return Z_CUP + CUP_DROP + (y - Y_CUP_BACK) * tan(radians(CHUTE_SLOPE))
    return Z_CUP + CUP_DROP * (y - YF) / (Y_CUP_BACK - YF)


def dog_pivot():
    """Blocking pawl pivot (front view, absolute): tangent lever from the nose, offset outboard."""
    return 0.5 * (DOG_TIP[0] + DOG_TIP[1]) + DOG_LEVER, Z_HANDLE + KNOB_R + DOG_OFFSET


def ratchet_pawl_geom():
    """(nose point, tangent, normal, pivot) of the anti-reverse pawl, front view absolute."""
    nx, nz = fv(RAT_R, RAT_PAWL_ANGLE)
    a = radians(RAT_PAWL_ANGLE)
    t = (cos(a), -sin(a))
    n = (sin(a), cos(a))
    N = (nx, Z_HANDLE + nz)
    P = (N[0] - 20.0 * t[0] + 6.0 * n[0], N[1] - 20.0 * t[1] + 6.0 * n[1])
    return N, t, n, P
