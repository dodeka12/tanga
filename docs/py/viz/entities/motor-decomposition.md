# Motor decomposition

A **motor** is a rigid-body motion written as a rotation followed by a
translation:

$$M = T(\mathbf{t})\;R(\theta, \hat{a})$$

where

- $R(\theta, \hat{a}) = c - s B$ is a rotor about the unit axis $\hat{a}$, with
  $c = \cos(\theta/2)$, $s = \sin(\theta/2)$, and $B$ the unit bivector of the
  rotation plane (the dual of $\hat{a}$);
- $T(\mathbf{t}) = 1 - \tfrac{1}{2}\,\mathbf{t} \wedge e_\infty$ is a
  translation by $\mathbf{t}$.

Every motor can be rewritten as a **screw**: a translation along the rotation
axis composed with a *general rotor* — a rotation about an axis that has been
displaced away from the origin:

$$M = T(\mathbf{u})\;\Bigl(T(\mathbf{v})\;R(\theta, \hat{a})\;\tilde T(\mathbf{v})\Bigr)
  = T(\mathbf{u})\;G(\theta, \hat{a}, \mathbf{v}).$$

`Motor` is stored internally in this normalized form: a `GeneralRotor`
(`angle`, `axis`, `origin`) plus a `Translator` whose vector lies along the
axis.

## Decomposition

Split the translation into a component along the axis and one perpendicular to
it:

$$\mathbf{u} = \mathbf{t}_\parallel = (\mathbf{t} \cdot \hat{a})\,\hat{a},
\qquad
\mathbf{t}_\perp = \mathbf{t} - \mathbf{u}.$$

The axis displacement $\mathbf{v}$ (perpendicular to the axis) is then

$$\mathbf{v} = \tfrac{1}{2}\Bigl(
  \mathbf{t}_\perp + \cot\tfrac{\theta}{2}\; \hat{a} \times \mathbf{t}_\perp
\Bigr).$$

The axial part $\mathbf{u}$ becomes the translation along the screw axis and
$\mathbf{v}$ becomes the origin of the general rotor.

## Special cases

- **Pure rotation** ($\mathbf{t} = 0$): $\mathbf{u} = \mathbf{v} = 0$.
- **Pure screw** ($\mathbf{t}_\perp = 0$): $\mathbf{v} = 0$, $\mathbf{u} = \mathbf{t}$.
- **Pure translation** ($\theta \approx 0$): the screw pitch is infinite and
  $\cot(\theta/2)$ diverges, so the code falls back to $\mathbf{u} = \mathbf{t}$,
  $\mathbf{v} = 0$ with an identity rotation.

## Worked example

Take $R(\pi/2, \hat z)$ and $\mathbf{t} = (1, 1, 1)$. Then

$$\mathbf{u} = (0, 0, 1), \qquad \mathbf{t}_\perp = (1, 1, 0),$$

and, because $\cot(\pi/4) = 1$,

$$\mathbf{v} = \tfrac{1}{2}\Bigl((1, 1, 0) + \hat z \times (1, 1, 0)\Bigr)
  = \tfrac{1}{2}\Bigl((1, 1, 0) + (-1, 1, 0)\Bigr)
  = (0, 1, 0).$$

The motor is therefore a $90^\circ$ rotation about the axis through $(0, 1, 0)$
parallel to $\hat z$, composed with a translation of $1$ along $\hat z$.
