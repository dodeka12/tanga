# Demostrate the use of the solver for the point-line matching problem in 3D.
# We have a set of 3D points that are projected onto a plane (camera image).
# We then rotate the points by a known rotation and add some noise to them.
# We then try to recover the original rotation using the solver.

import math
import numpy as np

from pytanga import BladeMask, EInv, EProduct, MV
from pytanga.algebra import from_rotor
from pytanga.basis.p3 import BasisP3
from pytanga.geometry import Direction, Point, Rotor, create_entity, create_operator
from pytanga.tensor import MVTensor, MVLabeledTensor
from pytanga.tensor.product import product_tensor
from pytanga.tensor.convert import to_tensor, from_tensor

try:
    from scipy.optimize import least_squares
except Exception:
    print("SciPy is not installed. Please run 'uv sync --extra example' or 'uv sync --group dev' to install.")
    exit(1)

P3 = BasisP3()


def _rnd_point() -> MV:
    return create_entity(
        P3,
        Point(
            P3.rng.uniform(-2, 2),
            P3.rng.uniform(-2, 2),
            P3.rng.uniform(-2, 2),
        ),
    )


def _rnd_direction() -> MV:
    return create_entity(
        P3,
        Direction(
            P3.rng.uniform(-0.1, 0.1),
            P3.rng.uniform(-0.1, 0.1),
            P3.rng.uniform(-0.1, 0.1),
        ),
    )


# Create random points
pnt_list: list[MV] = [_rnd_point() for _ in range(4)]
print("3D points:")
for pnt in pnt_list:
    pnt.show()

# Project the 3d points to an image plane perpendicular to e3 at e3 + e4.
origin: MV = create_entity(P3, Point(0, 0, 0))
plane: MV = (
    create_entity(P3, Point(0, 0, 1))
    ^ create_entity(P3, Point(1, 0, 1))
    ^ create_entity(P3, Point(0, 1, 1))
)
prj_ray_list: list[MV] = [origin ^ pnt for pnt in pnt_list]
prj_pnt_list: list[MV] = [ray | plane for ray in prj_ray_list]
print("Projections:")
for pnt in prj_pnt_list:
    pnt.show()

theta_true: float = math.radians(36.0)

rotor_true: MV = create_operator(
    P3, Rotor(angle=theta_true, axis=Direction(1, 1, 1).normalized())
)

# Rotate the points and add some noise to them
true_rot_pnt_list: list[MV] = [rotor_true.vp(pnt) for pnt in pnt_list]

rot_pnt_list: list[MV] = [
    pnt + _rnd_direction()
    for pnt in true_rot_pnt_list
]

# We are looking for the rotor that best maps the noisy rot_pnt_list back to pnt_list
# from just knowing the projection rays.
# We need to solve for the rotor R, such that ray_a ^ (R * p_a * ~R) = 0.
# The R is quadratic in this equation, so we cannot use the solver directly.
# Instead, we can calculate the Jacobean of the equation with respect to the rotor R
# and use that to solve for R iteratively.
# To derive the Jacobean, let's write (R * p_a * ~R) in tensor form:
# q_a^n = r^i p_a^j G^k_ij r^l Rev^m_l G^n_km, where Rev^m_l encodes the reverse on a rotor.
# The derivative of this with respect to r^i is:
# d q_a^n / d r^i = p_a^j G^k_ij r^l Rev^m_l G^n_km + r^l p_a^j G^k_lj Rev^m_i G^n_km

# Create the blade masks we need
pnt_mask: BladeMask = BladeMask(P3, "e1 + e2 + e3 + e4")
rot_mask: BladeMask = BladeMask(P3, "1 + e12 + e23 + e13")
ray_mask: BladeMask = BladeMask(P3, grades=[2])
plane_mask: BladeMask = BladeMask(P3, grades=[3])
scalar_mask: BladeMask = BladeMask(P3, (0,))

# Create product tensor for R * p_i
RP_t: MVTensor = product_tensor(rot_mask, pnt_mask, product=EProduct.GP)

# Now the product tensor for the geometric product in (R * p_i) * ~R
rpR_t: MVTensor = product_tensor(
    RP_t.masks[
        0
    ],  # The blade mask of the left product element is the result of the previous product.
    rot_mask,
    c_mask=pnt_mask,  # We know that the versor product of a rotor with a point must be a point.
    product=EProduct.GP,
    b_inv=EInv.REV,  # The right rotor has to be reversed.
)

# Now combine the two tensors
RPR_t: MVLabeledTensor = (RP_t["kij"] * rpR_t["lkm"])["->lijm"]
# This is equivalent to using the contract() function directly:
#   RPR_t: MVTensor = contract("kij,lkm->lijm", RP_t, rpR_t)

# The goal is to check whether a rotated point lies on a projection ray.
# This is done by taking the outer product of the ray with the points.
# The corresponding product tensor is:
Ray_Pnt_t: MVTensor = product_tensor(ray_mask, pnt_mask, product=EProduct.OP)

# The complete tensor is:
Ray_RPR_t: MVLabeledTensor = (Ray_Pnt_t["pql"] * RPR_t["lijm"])["->pqijm"]
# The direct call would be:
#   Ray_RPR_t: MVTensor = contract("pql,lijm->pqijm", Ray_Pnt_t, RPR_t)
# where:
#   p: result index (plane)
#   q: ray index
#   i: rotor index
#   j: point index
#   m: rotor index

# When contracting Ray_RPR_t with the ray and corresponding point and some rotor,
# It will in general result in a grade 3 blade, which is dual to a grade 1 vector.
# We are interested in minimzing the magnitude of these grade 3 blades.
# So the value to minimize is D = sum_n Plane_n * ~Plane_n.
#
# The derivative with respect to a Rotor R at a given R_0 is
# (d D / d R)(i) = sum_n d [(Plane_n / d R)(pi) * ~Plane_n(p) +
#                           Plane_n(p) * ~ (d Plane_n / d R)(pi)
# and we have the Jacobean:
# (d Plane_n / d R)(pi) = Ray_RPR_t(pqijm) * Ray_n(q) * Point_n(j) * R_0(m) +
#                         Ray_RPR_t(pqmji) * Ray_n(q) * Point_n(j) * R_0(m)
#

# The Plane * ~Plane product tensor:
PP_t: MVTensor = product_tensor(plane_mask, plane_mask, scalar_mask, product=EProduct.GP, b_inv=EInv.REV,)

# Convert the lists of points and rays to tensors
rot_pnt_t = to_tensor(rot_pnt_list, mask=pnt_mask)
ray_t = to_tensor(prj_ray_list, mask=ray_mask)

# Partially contract the tensor with the given data, i.e. the points and rays.
# The 'n_' index indicates that there should be no contraction over this index.
RR_t: MVLabeledTensor = (Ray_RPR_t["pqijm"] * rot_pnt_t["jn_"] * ray_t["qn_"])["->pimn"]

# Define the residual function
def residual(R_a: np.ndarray) -> np.ndarray:
    R_t = MVTensor(R_a, masks=[rot_mask])
    Plane_t = RR_t["pimn"] * R_t["i"] * R_t["m"]
    res_t = Plane_t.norm("p").sum("n")
    return res_t.data

def jacobean(R_a: np.ndarray) -> np.ndarray:
    R_t = MVTensor(R_a, masks=[rot_mask])
    Plane_t = RR_t["pimn"] * R_t["i"] * R_t["m"]
    dPlane_dR_t = (RR_t["pimn"] * R_t["m"]) + (RR_t["pmin"] * R_t["m"])
    dD_dR_t = (PP_t["kpq"] * dPlane_dR_t["pin_"] * Plane_t["qn_"] 
                + PP_t["kpq"] * Plane_t["pn_"] * dPlane_dR_t["qin_"])["->kin"]
    jac_t = dD_dR_t.sum("n")
    return jac_t.data[0]

# Create a starting rotor
rotor_start: MV = create_operator(P3, Rotor(angle=0.0, axis=Direction(1, 0, 0)))
rotor_start_t = to_tensor(rotor_start, mask=rot_mask)

# Run the least squares optimization
rotor_est_dict = least_squares(fun=residual, x0=rotor_start_t.data, jac=jacobean)
print(f"\nRotor estimation:\n{rotor_est_dict}")

# Get the tensor representation of the expected rotor, which is the 
# reverse of the true rotor from above.
rotor_exp = rotor_true.rev()
rotor_est_t = MVTensor(rotor_est_dict["x"], masks=[rot_mask])
rotor_est = from_tensor(rotor_est_t).normalized()

print(f"True rotor: {rotor_exp!s}")
print(f"Est. rotor: {rotor_est!s}")

scale_exp, angle_exp, plane_exp = from_rotor(rotor_exp)
scale_est, angle_est, plane_est = from_rotor(rotor_est)

print(f"Exp. : {scale_exp:.2f}, {math.degrees(angle_exp):.2f}, {plane_exp}")
print(f"Est. : {scale_est:.2f}, {math.degrees(angle_est):.2f}, {plane_est}")

