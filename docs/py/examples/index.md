# Examples

Runnable examples grouped by topic and searchable by keyword. Run any script with:

```bash
uv run python py/examples/<path>.py
```

## Keyword index

- **2D** — [2D orthographic view via View2DConfig](viz/camera/2d_view.md), [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md), [2D fit-camera keeps the axes/grid undistorted](viz/camera/fit_2d.md), [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md)

- **3D** — [3D projective camera via View3dConfig](viz/camera/3d_plane.md), [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md), [a plot on a tilted background plane in 3D](viz/plotting/plot_3d.md)

- **A X = B** — [Solve the general multivector equation A X = B with expressions](ga/expression/solve_ax_b.md)

- **ActPoint** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [Demo: Drag a 3D point interactively with ActPoint](viz/interaction/act_point.md), [Demo: Drag TWO 3D points interactively with ActPoint](viz/interaction/act_point_two.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md)

- **add_control_group** — [Unified control groups: overlay-anchored + 3D-anchored](viz/scenes/control_group_overlay.md), [Unified control groups on a single-scene page](viz/scenes/control_group_single.md)

- **add_table** — [An editable tabular-data control driven by the backend](viz/interaction/table_data.md), [An editable table with spreadsheet-style keyboard editing](viz/interaction/table_editing.md)

- **affine** — [Polynomial (repeated-variable) expressions and affine sums](ga/expression/polynomial_demo.md)

- **alert** — [Demonstrates every banner/dialog kind](viz/banners/banner_types.md), [Banners scoped to a named scene via VizSceneHandle](viz/banners/scene_banner.md)

- **Algebra** — [How pytanga builds C++ backends on the fly](binding_demo.md), [Creating and configuring an Algebra](ga/algebra/algebra_demo.md), [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md), [Integer GA with a single modulus (Path C)](ga/algebra/modulus_algebra_single.md)

- **align modes** — [Demo: Texture labels on planes with different align modes](viz/labels/texture_plane.md)

- **all types** — [All geometric entity types in one scene](viz/entities/all_entities.md)

- **anchor** — [Unified control groups: overlay-anchored + 3D-anchored](viz/scenes/control_group_overlay.md), [Unified control groups on a single-scene page](viz/scenes/control_group_single.md)

- **angle vs time** — [a swinging pendulum with a live angle-vs-time plot](viz/plotting/pendulum_plot.md)

- **animate** — [Animation](ga/jupyter/animation.md), [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md)

- **animate_to** — [Keyframe timeline with fade-in and move](viz/animation/timeline.md)

- **animated** — [Animated HTML export with JS playback engine](viz/export/animated.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md)

- **animation** — [Animation](ga/jupyter/animation.md), [A chaotic double pendulum from nested VizGroups](viz/animation/double_pendulum.md), [Nested animation loops honoring Ctrl+C](viz/animation/nested_sweep.md), [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md), [Moving point with a color-gradient trail](viz/animation/point_path_trail.md), [Keyframe timeline with fade-in and move](viz/animation/timeline.md), [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md), [SDF object groups with per-member CSG + independent animation](viz/sdf/group.md), [Animate a directional light around a sphere](viz/sdf/light_animation.md)

- **annotation** — [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md)

- **annotations** — [annotations in a CoordinateSystem's data frame](viz/plotting/cs_annotations.md)

- **app** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md)

- **Arc** — [the visualization-only Cylinder and Arc entities](viz/entities/viz_entities.md)

- **arrowhead** — [isolate the SDF arrowhead (capped cone) placement](viz/sdf/arrowhead.md)

- **auto-fit** — [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md)

- **auto_clear** — [Animation](ga/jupyter/animation.md)

- **Axes2D** — [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md)

- **Axis** — [Custom axes and grid as explicit scene objects](viz/plotting/axes_custom.md)

- **banner** — [Demonstrates every banner/dialog kind](viz/banners/banner_types.md), [Slider that triggers a blocking computation on release](viz/banners/heavy_work.md), [Banners scoped to a named scene via VizSceneHandle](viz/banners/scene_banner.md)

- **bar** — [Menus: global hamburger, per-pane overlay, sub-menu, and a bar](viz/menus/menu_demo.md)

- **basis** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md)

- **basis blades** — [Three ways to work with named basis blades](ga/basis/basis_usage.md)

- **BasisE3** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md), [Three ways to work with named basis blades](ga/basis/basis_usage.md)

- **BasisN3** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md)

- **BasisP3** — [Projective 3D geometric algebra  G(4, 0)](ga/basis/base_p3_demo.md)

- **BasisPGA3** — [Projective GA  (PGA 3D)](ga/basis/base_pga3_demo.md)

- **batched** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md)

- **binding** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **BladeMask** — [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md)

- **Box** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **button** — [Showcase every interactive control in one app](viz/interaction/all_controls.md), [Controls styled from the extracted theme CSS files](viz/scenes/control_theming.md)

- **C++ backend** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **cache** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **camera** — [2D orthographic view via View2DConfig](viz/camera/2d_view.md), [3D projective camera via View3dConfig](viz/camera/3d_plane.md), [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md), [2D fit-camera keeps the axes/grid undistorted](viz/camera/fit_2d.md), [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md)

- **capped cone** — [isolate the SDF arrowhead (capped cone) placement](viz/sdf/arrowhead.md)

- **cell editing** — [An editable table with spreadsheet-style keyboard editing](viz/interaction/table_editing.md)

- **chaos** — [A chaotic double pendulum from nested VizGroups](viz/animation/double_pendulum.md)

- **checkbox** — [Controls styled from the extracted theme CSS files](viz/scenes/control_theming.md)

- **Circle** — [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md)

- **click** — [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md)

- **code generation** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **coefficients** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md)

- **combine** — [per-object CSG combine modes](viz/sdf/booleans.md)

- **comparison** — [every solid object as a mesh next to its SDF twin](viz/sdf/mesh_vs_sdf_grid.md)

- **compilation** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **Composed** — [Composed SDF objects + the primitive library](viz/sdf/composed.md)

- **confirm** — [Demonstrates every banner/dialog kind](viz/banners/banner_types.md), [Banners scoped to a named scene via VizSceneHandle](viz/banners/scene_banner.md)

- **conformal** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md), [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md), [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md)

- **constraints** — [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md)

- **construction** — [Three ways to work with named basis blades](ga/basis/basis_usage.md)

- **context manager** — [Interactive Visualizer](ga/jupyter/interactive.md), [Two named scenes, each shown in its own browser tab](viz/scenes/multi_scene.md)

- **control group** — [Unified control groups: overlay-anchored + 3D-anchored](viz/scenes/control_group_overlay.md), [Unified control groups on a single-scene page](viz/scenes/control_group_single.md)

- **controls** — [Showcase every interactive control in one app](viz/interaction/all_controls.md), [A file chooser with a backend-driven file browser](viz/interaction/file_chooser.md), [An editable tabular-data control driven by the backend](viz/interaction/table_data.md), [An editable table with spreadsheet-style keyboard editing](viz/interaction/table_editing.md), [Controls styled from the extracted theme CSS files](viz/scenes/control_theming.md), [A horizontal control toolbar nested inside a vertical stack](viz/scenes/toolbar.md)

- **CoordinateSystem** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [annotations in a CoordinateSystem's data frame](viz/plotting/cs_annotations.md), [logarithmic plotting with CoordinateSystem](viz/plotting/log_plot.md)

- **CSG** — [per-object CSG combine modes](viz/sdf/booleans.md), [SDF object groups with per-member CSG + independent animation](viz/sdf/group.md)

- **css** — [Controls styled from the extracted theme CSS files](viz/scenes/control_theming.md)

- **Ctrl+C** — [Nested animation loops honoring Ctrl+C](viz/animation/nested_sweep.md)

- **custom intervals** — [Custom axes and grid as explicit scene objects](viz/plotting/axes_custom.md)

- **Cylinder** — [the visualization-only Cylinder and Arc entities](viz/entities/viz_entities.md)

- **defaults** — [Global default styles and per-call overrides](viz/styling/custom_defaults.md)

- **dialog** — [Demonstrates every banner/dialog kind](viz/banners/banner_types.md), [A titled dialog whose body holds view-based controls](viz/dialogs/dialog_demo.md)

- **Dilator** — [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md)

- **dimension** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md)

- **Direction** — [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md)

- **Disk** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **display** — [Interactive Visualizer](ga/jupyter/interactive.md)

- **double pendulum** — [A chaotic double pendulum from nested VizGroups](viz/animation/double_pendulum.md)

- **drag** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [Demo: Drag a 3D point interactively with ActPoint](viz/interaction/act_point.md), [Demo: Drag TWO 3D points interactively with ActPoint](viz/interaction/act_point_two.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md), [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md)

- **dropdown** — [Showcase every interactive control in one app](viz/interaction/all_controls.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md), [Menus: global hamburger, per-pane overlay, sub-menu, and a bar](viz/menus/menu_demo.md)

- **dtype** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md)

- **dual modulus** — [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md)

- **E3** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md), [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **easing** — [Keyframe timeline with fade-in and move](viz/animation/timeline.md)

- **einsum** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **Ellipse** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **Ellipsoid** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **entities** — [All geometric entity types in one scene](viz/entities/all_entities.md), [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md), [the visualization-only Cylinder and Arc entities](viz/entities/viz_entities.md), [First vertical slice for the SDF viewer](viz/sdf/entities.md)

- **entity** — [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md)

- **Euclidean** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md)

- **explicit** — [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md)

- **export** — [Export](ga/jupyter/export.md), [Animated HTML export with JS playback engine](viz/export/animated.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md), [Presentation figure export with FigureStyle](viz/export/figure.md), [Self-contained HTML and glTF export](viz/export/html_export.md), [Programmatic PNG screenshot at custom resolution](viz/export/screenshot.md)

- **expressions** — [Multi-variable linear equations with Variables](ga/expression/equation_demo.md), [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md), [Polynomial (repeated-variable) expressions and affine sums](ga/expression/polynomial_demo.md), [Solve the general multivector equation A X = B with expressions](ga/expression/solve_ax_b.md), [Apply a fixed rotor to points with a Variable-backed expression](ga/expression/variable_rotor.md), [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md)

- **figure** — [Export](ga/jupyter/export.md), [Presentation figure export with FigureStyle](viz/export/figure.md)

- **FigureStyle** — [Presentation figure export with FigureStyle](viz/export/figure.md)

- **file browser** — [A file chooser with a backend-driven file browser](viz/interaction/file_chooser.md)

- **file chooser** — [A file chooser with a backend-driven file browser](viz/interaction/file_chooser.md)

- **first slice** — [First vertical slice for the SDF viewer](viz/sdf/entities.md)

- **fit camera** — [2D fit-camera keeps the axes/grid undistorted](viz/camera/fit_2d.md)

- **fixed modulus** — [Integer GA with a single modulus (Path C)](ga/algebra/modulus_algebra_single.md)

- **fold** — [Group view chrome: leading icon, icon-only, borderless fold](viz/scenes/group_view_icons.md)

- **frame streaming** — [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md)

- **G(3,0)** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md)

- **G(3,1)** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md)

- **G(4,0)** — [Projective 3D geometric algebra  G(4, 0)](ga/basis/base_p3_demo.md)

- **G(5,0b10000)** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md)

- **general solve** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_01.md), [Core solver API: inverse and general solve](ga/numerics/solver_basics_02.md)

- **geometric product** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md)

- **geometry** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md)

- **glTF** — [Export](ga/jupyter/export.md), [Self-contained HTML and glTF export](viz/export/html_export.md)

- **gradient** — [Moving point with a color-gradient trail](viz/animation/point_path_trail.md)

- **gravity** — [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md)

- **Grid** — [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md), [Custom axes and grid as explicit scene objects](viz/plotting/axes_custom.md)

- **group** — [SDF object groups with per-member CSG + independent animation](viz/sdf/group.md)

- **group view** — [Group view chrome: leading icon, icon-only, borderless fold](viz/scenes/group_view_icons.md)

- **Gunn/Dorst** — [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md)

- **heavy work** — [Slider that triggers a blocking computation on release](viz/banners/heavy_work.md)

- **hierarchy** — [Demonstrate nested VizGroup hierarchies](viz/scenes/nested_groups.md)

- **homogeneous** — [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md)

- **horizontal** — [A horizontal control toolbar nested inside a vertical stack](viz/scenes/toolbar.md)

- **HTML** — [Export](ga/jupyter/export.md), [Animated HTML export with JS playback engine](viz/export/animated.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md), [Self-contained HTML and glTF export](viz/export/html_export.md)

- **icon** — [Group view chrome: leading icon, icon-only, borderless fold](viz/scenes/group_view_icons.md)

- **icon_only** — [Controls styled from the extracted theme CSS files](viz/scenes/control_theming.md), [Group view chrome: leading icon, icon-only, borderless fold](viz/scenes/group_view_icons.md)

- **initialization** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md)

- **integer** — [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md), [Integer GA with a single modulus (Path C)](ga/algebra/modulus_algebra_single.md)

- **interaction** — [Demo: Drag a 3D point interactively with ActPoint](viz/interaction/act_point.md), [Demo: Drag TWO 3D points interactively with ActPoint](viz/interaction/act_point_two.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md), [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md)

- **interactive** — [Interactive Visualizer](ga/jupyter/interactive.md)

- **inverse** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_01.md), [Core solver API: inverse and general solve](ga/numerics/solver_basics_02.md)

- **Inversion** — [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md)

- **IPNS** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md)

- **KaTeX** — [Demo: Texture labels on spheres using plain text and KaTeX formulas](viz/labels/texture_sphere.md), [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md)

- **keyboard navigation** — [An editable table with spreadsheet-style keyboard editing](viz/interaction/table_editing.md)

- **keyframe** — [Keyframe timeline with fade-in and move](viz/animation/timeline.md)

- **labels** — [Labels with custom styling, dynamic update, and removal](viz/labels/basic.md)

- **LabelStyle** — [Labels with custom styling, dynamic update, and removal](viz/labels/basic.md)

- **LaTeX** — [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md)

- **layout** — [Menus: global hamburger, per-pane overlay, sub-menu, and a bar](viz/menus/menu_demo.md), [Unified control groups: overlay-anchored + 3D-anchored](viz/scenes/control_group_overlay.md), [Three scenes side-by-side in one horizontal split](viz/scenes/multi_split.md), [A single page showing multiple scenes in split panes](viz/scenes/split_view.md), [A horizontal control toolbar nested inside a vertical stack](viz/scenes/toolbar.md)

- **least-norm** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md)

- **least-squares** — [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md), [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md), [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Best-fit rotor from point correspondences](ga/numerics/solver_rotor_estimation.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md)

- **light** — [Animate a directional light around a sphere](viz/sdf/light_animation.md)

- **Line** — [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [All geometric entity types in one scene](viz/entities/all_entities.md)

- **line fitting** — [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md), [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md)

- **linear equations** — [Multi-variable linear equations with Variables](ga/expression/equation_demo.md)

- **linear system** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_01.md)

- **live plot** — [a swinging pendulum with a live angle-vs-time plot](viz/plotting/pendulum_plot.md)

- **log plot** — [logarithmic plotting with CoordinateSystem](viz/plotting/log_plot.md)

- **low-level** — [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md)

- **Markdown** — [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md)

- **menu** — [Menus: global hamburger, per-pane overlay, sub-menu, and a bar](viz/menus/menu_demo.md)

- **menu bar** — [A titled dialog whose body holds view-based controls](viz/dialogs/dialog_demo.md)

- **mesh** — [every solid object as a mesh next to its SDF twin](viz/sdf/mesh_vs_sdf_grid.md)

- **meshes** — [Mix standard meshes with SDF-styled objects](viz/sdf/objects.md)

- **modal** — [Slider that triggers a blocking computation on release](viz/banners/heavy_work.md), [A titled dialog whose body holds view-based controls](viz/dialogs/dialog_demo.md)

- **modes** — [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md)

- **modulus** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md), [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md), [Integer GA with a single modulus (Path C)](ga/algebra/modulus_algebra_single.md)

- **Motor** — [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md), [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md)

- **multi-pane** — [Three scenes side-by-side in one horizontal split](viz/scenes/multi_split.md)

- **multi-scene** — [Two named scenes, each shown in its own browser tab](viz/scenes/multi_scene.md)

- **multivector** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md)

- **multivector equation** — [Solve the general multivector equation A X = B with expressions](ga/expression/solve_ax_b.md)

- **MV** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md)

- **MVTensor** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md)

- **N3** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md), [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md), [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md)

- **named blades** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md), [Three ways to work with named basis blades](ga/basis/basis_usage.md)

- **nested** — [Demonstrate nested VizGroup hierarchies](viz/scenes/nested_groups.md)

- **nested loops** — [Nested animation loops honoring Ctrl+C](viz/animation/nested_sweep.md)

- **notebook** — [Animation](ga/jupyter/animation.md), [Export](ga/jupyter/export.md), [Interactive Visualizer](ga/jupyter/interactive.md)

- **NTRU** — [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md)

- **null vector** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md), [Projective GA  (PGA 3D)](ga/basis/base_pga3_demo.md)

- **object model** — [the unified SDF object model in the standard viewer](viz/sdf/object_model.md)

- **on_close** — [A titled dialog whose body holds view-based controls](viz/dialogs/dialog_demo.md)

- **on_release** — [Slider that triggers a blocking computation on release](viz/banners/heavy_work.md)

- **operators** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md)

- **OPNS** — [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md)

- **orbit** — [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md)

- **orthographic** — [2D orthographic view via View2DConfig](viz/camera/2d_view.md), [2D fit-camera keeps the axes/grid undistorted](viz/camera/fit_2d.md)

- **overlay** — [Menus: global hamburger, per-pane overlay, sub-menu, and a bar](viz/menus/menu_demo.md), [Unified control groups: overlay-anchored + 3D-anchored](viz/scenes/control_group_overlay.md), [Unified control groups on a single-scene page](viz/scenes/control_group_single.md), [Group view chrome: leading icon, icon-only, borderless fold](viz/scenes/group_view_icons.md)

- **overrides** — [Global default styles and per-call overrides](viz/styling/custom_defaults.md)

- **P2** — [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md)

- **P3** — [Projective 3D geometric algebra  G(4, 0)](ga/basis/base_p3_demo.md), [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md), [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md)

- **panes** — [Three scenes side-by-side in one horizontal split](viz/scenes/multi_split.md), [A single page showing multiple scenes in split panes](viz/scenes/split_view.md)

- **parent_id** — [Unified control groups: overlay-anchored + 3D-anchored](viz/scenes/control_group_overlay.md), [Unified control groups on a single-scene page](viz/scenes/control_group_single.md)

- **PartialDisk** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **pendulum** — [a swinging pendulum with a live angle-vs-time plot](viz/plotting/pendulum_plot.md)

- **PGA3** — [Projective GA  (PGA 3D)](ga/basis/base_pga3_demo.md), [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md)

- **Plane** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [All geometric entity types in one scene](viz/entities/all_entities.md)

- **plane** — [Demo: Texture labels on planes with different align modes](viz/labels/texture_plane.md)

- **plane-based** — [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md)

- **playback** — [Animated HTML export with JS playback engine](viz/export/animated.md)

- **plotting** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [Custom axes and grid as explicit scene objects](viz/plotting/axes_custom.md), [annotations in a CoordinateSystem's data frame](viz/plotting/cs_annotations.md), [logarithmic plotting with CoordinateSystem](viz/plotting/log_plot.md), [a swinging pendulum with a live angle-vs-time plot](viz/plotting/pendulum_plot.md), [a plot on a tilted background plane in 3D](viz/plotting/plot_3d.md)

- **PNG** — [Programmatic PNG screenshot at custom resolution](viz/export/screenshot.md)

- **Point** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md), [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md), [All geometric entity types in one scene](viz/entities/all_entities.md)

- **point** — [Demo: Drag a 3D point interactively with ActPoint](viz/interaction/act_point.md), [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md)

- **point correspondences** — [Best-fit rotor from point correspondences](ga/numerics/solver_rotor_estimation.md)

- **Point Pair** — [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md)

- **point-line matching** — [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md)

- **PointPath** — [Moving point with a color-gradient trail](viz/animation/point_path_trail.md)

- **points** — [Apply a fixed rotor to points with a Variable-backed expression](ga/expression/variable_rotor.md), [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md)

- **polarity** — [per-object CSG combine modes](viz/sdf/booleans.md)

- **polynomial** — [Polynomial (repeated-variable) expressions and affine sums](ga/expression/polynomial_demo.md)

- **presentation** — [Presentation figure export with FigureStyle](viz/export/figure.md)

- **primitive library** — [Composed SDF objects + the primitive library](viz/sdf/composed.md)

- **product tensor** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **projective** — [Projective 3D geometric algebra  G(4, 0)](ga/basis/base_p3_demo.md), [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md)

- **projective geometric algebra** — [Projective GA  (PGA 3D)](ga/basis/base_pga3_demo.md)

- **Reflection** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md)

- **remove** — [Labels with custom styling, dynamic update, and removal](viz/labels/basic.md)

- **remove_dialog** — [A titled dialog whose body holds view-based controls](viz/dialogs/dialog_demo.md)

- **repeated variables** — [Polynomial (repeated-variable) expressions and affine sums](ga/expression/polynomial_demo.md)

- **residual** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_02.md)

- **rotor** — [Apply a fixed rotor to points with a Variable-backed expression](ga/expression/variable_rotor.md), [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **Rotor** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md)

- **rotor estimation** — [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Best-fit rotor from point correspondences](ga/numerics/solver_rotor_estimation.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md)

- **row delete** — [An editable table with spreadsheet-style keyboard editing](viz/interaction/table_editing.md)

- **scene** — [Banners scoped to a named scene via VizSceneHandle](viz/banners/scene_banner.md)

- **scene graph** — [Demonstrate VizGroup + direct transforms](viz/scenes/scene_graph.md)

- **scenes** — [Menus: global hamburger, per-pane overlay, sub-menu, and a bar](viz/menus/menu_demo.md), [Controls styled from the extracted theme CSS files](viz/scenes/control_theming.md), [Group view chrome: leading icon, icon-only, borderless fold](viz/scenes/group_view_icons.md), [Two named scenes, each shown in its own browser tab](viz/scenes/multi_scene.md), [Three scenes side-by-side in one horizontal split](viz/scenes/multi_split.md), [Demonstrate nested VizGroup hierarchies](viz/scenes/nested_groups.md), [Demonstrate VizGroup + direct transforms](viz/scenes/scene_graph.md), [A single page showing multiple scenes in split panes](viz/scenes/split_view.md), [An editable data table beside a 3D scene](viz/scenes/table_split.md), [A horizontal control toolbar nested inside a vertical stack](viz/scenes/toolbar.md)

- **screenshot** — [Programmatic PNG screenshot at custom resolution](viz/export/screenshot.md)

- **SDF** — [isolate the SDF arrowhead (capped cone) placement](viz/sdf/arrowhead.md), [per-object CSG combine modes](viz/sdf/booleans.md), [Composed SDF objects + the primitive library](viz/sdf/composed.md), [First vertical slice for the SDF viewer](viz/sdf/entities.md), [SDF object groups with per-member CSG + independent animation](viz/sdf/group.md), [Animate a directional light around a sphere](viz/sdf/light_animation.md), [every solid object as a mesh next to its SDF twin](viz/sdf/mesh_vs_sdf_grid.md), [the unified SDF object model in the standard viewer](viz/sdf/object_model.md), [Mix standard meshes with SDF-styled objects](viz/sdf/objects.md)

- **set_default_color** — [Global default styles and per-call overrides](viz/styling/custom_defaults.md)

- **show** — [Interactive Visualizer](ga/jupyter/interactive.md)

- **show_dialog** — [A titled dialog whose body holds view-based controls](viz/dialogs/dialog_demo.md)

- **signature** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md)

- **simulation** — [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md)

- **single scene** — [Unified control groups on a single-scene page](viz/scenes/control_group_single.md)

- **singular** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md)

- **slider** — [Slider that triggers a blocking computation on release](viz/banners/heavy_work.md), [Showcase every interactive control in one app](viz/interaction/all_controls.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md), [Controls styled from the extracted theme CSS files](viz/scenes/control_theming.md)

- **snapshot** — [Export](ga/jupyter/export.md), [Self-contained HTML and glTF export](viz/export/html_export.md)

- **solve** — [Solve the general multivector equation A X = B with expressions](ga/expression/solve_ax_b.md)

- **solve_lsq** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md)

- **solver** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_01.md), [Core solver API: inverse and general solve](ga/numerics/solver_basics_02.md), [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md), [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md), [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Best-fit rotor from point correspondences](ga/numerics/solver_rotor_estimation.md)

- **Sphere** — [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md), [All geometric entity types in one scene](viz/entities/all_entities.md)

- **sphere** — [Demo: Texture labels on spheres using plain text and KaTeX formulas](viz/labels/texture_sphere.md), [Animate a directional light around a sphere](viz/sdf/light_animation.md)

- **spheres** — [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md)

- **split view** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [Three scenes side-by-side in one horizontal split](viz/scenes/multi_split.md), [A single page showing multiple scenes in split panes](viz/scenes/split_view.md), [An editable data table beside a 3D scene](viz/scenes/table_split.md)

- **stack view** — [A horizontal control toolbar nested inside a vertical stack](viz/scenes/toolbar.md)

- **StackView** — [A titled dialog whose body holds view-based controls](viz/dialogs/dialog_demo.md)

- **standard viewer** — [the unified SDF object model in the standard viewer](viz/sdf/object_model.md)

- **styled objects** — [Mix standard meshes with SDF-styled objects](viz/sdf/objects.md)

- **styling** — [Global default styles and per-call overrides](viz/styling/custom_defaults.md)

- **sub-menu** — [Menus: global hamburger, per-pane overlay, sub-menu, and a bar](viz/menus/menu_demo.md)

- **sweep** — [Nested animation loops honoring Ctrl+C](viz/animation/nested_sweep.md)

- **table** — [An editable tabular-data control driven by the backend](viz/interaction/table_data.md), [An editable table with spreadsheet-style keyboard editing](viz/interaction/table_editing.md), [An editable data table beside a 3D scene](viz/scenes/table_split.md)

- **TableView** — [An editable data table beside a 3D scene](viz/scenes/table_split.md)

- **tabs** — [Two named scenes, each shown in its own browser tab](viz/scenes/multi_scene.md)

- **tabular data** — [An editable tabular-data control driven by the backend](viz/interaction/table_data.md), [An editable table with spreadsheet-style keyboard editing](viz/interaction/table_editing.md), [An editable data table beside a 3D scene](viz/scenes/table_split.md)

- **tensor** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **texture labels** — [Demo: Texture labels on planes with different align modes](viz/labels/texture_plane.md), [Demo: Texture labels on spheres using plain text and KaTeX formulas](viz/labels/texture_sphere.md)

- **theme** — [Controls styled from the extracted theme CSS files](viz/scenes/control_theming.md)

- **tilted plane** — [a plot on a tilted background plane in 3D](viz/plotting/plot_3d.md)

- **timeline** — [Keyframe timeline with fade-in and move](viz/animation/timeline.md)

- **title** — [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md)

- **toolbar** — [A horizontal control toolbar nested inside a vertical stack](viz/scenes/toolbar.md)

- **trail** — [Moving point with a color-gradient trail](viz/animation/point_path_trail.md)

- **transforms** — [Demonstrate VizGroup + direct transforms](viz/scenes/scene_graph.md)

- **Translator** — [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md)

- **two points** — [Demo: Drag TWO 3D points interactively with ActPoint](viz/interaction/act_point_two.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md)

- **two-body** — [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md)

- **up vector** — [3D projective camera via View3dConfig](viz/camera/3d_plane.md)

- **update** — [Labels with custom styling, dynamic update, and removal](viz/labels/basic.md)

- **update in place** — [Animation](ga/jupyter/animation.md)

- **Variable** — [Multi-variable linear equations with Variables](ga/expression/equation_demo.md), [Apply a fixed rotor to points with a Variable-backed expression](ga/expression/variable_rotor.md), [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md)

- **variables** — [Multi-variable linear equations with Variables](ga/expression/equation_demo.md)

- **View2DConfig** — [2D orthographic view via View2DConfig](viz/camera/2d_view.md), [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md)

- **View3dConfig** — [3D projective camera via View3dConfig](viz/camera/3d_plane.md)

- **visualization** — [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md)

- **visualization-only** — [the visualization-only Cylinder and Arc entities](viz/entities/viz_entities.md)

- **visualizer** — [Interactive Visualizer](ga/jupyter/interactive.md)

- **Visualizer** — [Demonstrates every banner/dialog kind](viz/banners/banner_types.md)

- **VisualizerApp** — [Slider that triggers a blocking computation on release](viz/banners/heavy_work.md), [Showcase every interactive control in one app](viz/interaction/all_controls.md), [A file chooser with a backend-driven file browser](viz/interaction/file_chooser.md), [An editable tabular-data control driven by the backend](viz/interaction/table_data.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md)

- **VizGroup** — [A chaotic double pendulum from nested VizGroups](viz/animation/double_pendulum.md), [Demonstrate nested VizGroup hierarchies](viz/scenes/nested_groups.md), [Demonstrate VizGroup + direct transforms](viz/scenes/scene_graph.md)

- **VizSceneHandle** — [Banners scoped to a named scene via VizSceneHandle](viz/banners/scene_banner.md)

## Topics

- [Geometric Algebra](ga/index.md)
- [Visualization](viz/index.md)
