# Examples

Runnable examples grouped by topic and searchable by keyword. Run any script with:

```bash
uv run python py/examples/<path>.py
```

## Keyword index

- **2D** — [2D orthographic view via View2DConfig](viz/camera/2d_view.md), [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md), [fixed screen-space axes + grid overlay in 2D](viz/camera/axes_overlay_2d.md), [2D fit-camera keeps the axes/grid undistorted](viz/camera/fit_2d.md), [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md), [Toggle one scene between a 2D and 3D view with a checkbox](viz/camera/switch_2d_3d.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md), [2D plots across a split view, one stretch mode per pane](viz/plotting/multi_plot.md)

- **3D** — [3D projective camera via View3dConfig](viz/camera/3d_plane.md), [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md), [Toggle one scene between a 2D and 3D view with a checkbox](viz/camera/switch_2d_3d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md), [a plot on a tilted background plane in 3D](viz/plotting/plot_3d.md)

- **A X = B** — [Solve the general multivector equation A X = B with expressions](ga/expression/solve_ax_b.md)

- **ActPoint** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [Demo: Drag a 3D point interactively with ActPoint](viz/interaction/act_point.md), [Demo: Drag TWO 3D points interactively with ActPoint](viz/interaction/act_point_two.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md)

- **ActRectangle2D** — [Add and drag rectangles on an image via a toolbar](viz/image/rectangle_labeling.md)

- **affine** — [Polynomial (repeated-variable) expressions and affine sums](ga/expression/polynomial_demo.md)

- **AffineExpression** — [Sum an AffineExpression over a batched variable](ga/expression/affine_counting_reduction.md), [Solve a single-linear-map AffineExpression](ga/expression/affine_linear_solve.md)

- **alert** — [Demonstrates every banner/dialog kind](viz/ui/banners/banner_types.md), [Banners scoped to a named scene via VizSceneHandle](viz/ui/banners/scene_banner.md)

- **Algebra** — [How pytanga builds C++ backends on the fly](binding_demo.md), [Creating and configuring an Algebra](ga/algebra/algebra_demo.md), [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md), [Integer GA with a single modulus (Path C)](ga/algebra/modulus_algebra_single.md)

- **align** — [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md)

- **align modes** — [Demo: Texture labels on planes with different align modes](viz/labels/texture_plane.md)

- **alignment** — [Four toolbars, one per alignment, stacked in a vertical split](viz/ui/controls/toolbar.md)

- **all types** — [All geometric entity types in one scene](viz/entities/all_entities.md)

- **analyze** — [reconstruct a conic from 5 points and rotate it with a slider](ga/quadric/conic_demo.md), [degenerate quadric (plane pair) analysis + rendering](ga/quadric/plane_pair_demo.md), [Q3 point tuples (1–7 points) in distinct colors](ga/quadric/point_tuples_demo.md), [reconstruct a quadric from 9 points and rotate it](ga/quadric/quadric3d_demo.md), [reconstruct a quadric from 9 points and ray-render it](ga/quadric/quadric3d_raycast.md)

- **anchor** — [Declarative control groups: overlay + 3D-anchored](viz/ui/controls/control_group_overlay.md), [Declarative control groups on a single-scene page](viz/ui/controls/control_group_single.md)

- **angle vs time** — [a swinging pendulum with a live angle-vs-time plot](viz/plotting/pendulum_plot.md)

- **animate** — [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md), [Animation](viz/jupyter/animation.md)

- **animate_to** — [Keyframe timeline with fade-in and move](viz/animation/timeline.md)

- **animated** — [Animated HTML export with JS playback engine](viz/export/animated.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md)

- **animation** — [A chaotic double pendulum from nested VizGroups](viz/animation/double_pendulum.md), [Nested animation loops honoring Ctrl+C](viz/animation/nested_sweep.md), [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md), [Moving point with a color-gradient trail](viz/animation/point_path_trail.md), [Keyframe timeline with fade-in and move](viz/animation/timeline.md), [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md), [Animation](viz/jupyter/animation.md), [Drive a VizGroup transform from a BasisN3 Motor](viz/scenes/motor_group_transform.md), [SDF object groups with per-member CSG + independent animation](viz/sdf/group.md), [Animate a directional light around a sphere](viz/sdf/light_animation.md)

- **annotation** — [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md), [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md), [A menu bar with a File → Open… file dialog](viz/ui/menus/file_open_menu.md)

- **annotations** — [annotations in a CoordinateSystem's data frame](viz/plotting/cs_annotations.md)

- **app** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md)

- **Arc** — [the visualization-only Cylinder and Arc entities](viz/entities/viz_entities.md)

- **arrowhead** — [isolate the SDF arrowhead (capped cone) placement](viz/sdf/arrowhead.md)

- **auto reload** — [Load a custom theme and edit it live](viz/ui/themes/custom_theme_autoreload.md)

- **auto-fit** — [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md)

- **auto-save** — [Table auto-save: JSON load/save + CSV export](viz/ui/controls/table_file.md)

- **auto_clear** — [Animation](viz/jupyter/animation.md)

- **axes** — [fixed screen-space axes + grid overlay in 2D](viz/camera/axes_overlay_2d.md)

- **Axes2D** — [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md)

- **Axis** — [Custom axes and grid as explicit scene objects](viz/plotting/axes_custom.md)

- **banner** — [Demonstrates every banner/dialog kind](viz/ui/banners/banner_types.md), [Slider that triggers a blocking computation on release](viz/ui/banners/heavy_work.md), [Banners scoped to a named scene via VizSceneHandle](viz/ui/banners/scene_banner.md)

- **bar** — [Menus: per-pane overlay, sub-menus, and sub-sub-menus](viz/ui/menus/menu_demo.md)

- **basis** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md), [BladeMask named bases (auto display basis, composed names, with_basis)](ga/blade_mask/named_basis.md), [get_tensor() (raw MVTensor) + get_array() (named bases)](ga/expression/tensor_named_basis.md)

- **basis blades** — [Three ways to work with named basis blades](ga/basis/basis_usage.md)

- **BasisE3** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md), [Three ways to work with named basis blades](ga/basis/basis_usage.md)

- **BasisN3** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md), [Drive a VizGroup transform from a BasisN3 Motor](viz/scenes/motor_group_transform.md)

- **BasisP3** — [Projective 3D geometric algebra  G(4, 0)](ga/basis/base_p3_demo.md)

- **BasisPGA3** — [Projective GA  (PGA 3D)](ga/basis/base_pga3_demo.md)

- **batched** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md)

- **bind** — [Bind a variable to a sub-expression (composition)](ga/expression/bind_subexpression.md), [Re-key variables so independent expressions merge](ga/expression/rename_unify_variables.md)

- **binding** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **BladeMask** — [BladeMask named bases (auto display basis, composed names, with_basis)](ga/blade_mask/named_basis.md), [Project an N3 expression onto the Euclidean basis](ga/expression/project_onto_euclidean_n3.md), [get_tensor() (raw MVTensor) + get_array() (named bases)](ga/expression/tensor_named_basis.md), [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md)

- **BOP** — [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md)

- **Box** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **button** — [Showcase every interactive control in one app](viz/ui/controls/all_controls.md), [Controls styled from the extracted theme CSS files](viz/ui/controls/control_theming.md), [A custom theme with a full button/checkbox override](viz/ui/themes/custom_theme_override.md)

- **ButtonView** — [Declarative controls drive a sphere](viz/ui/controls/controls_add_and_view.md)

- **C++ backend** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **cache** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **calibration** — [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md), [a calibrated camera as a free orbit/pan/zoom view](viz/camera/pinhole_camera.md), [calibrated camera view (image) + default 3D overview](viz/camera/pinhole_overlay.md)

- **camera** — [2D orthographic view via View2DConfig](viz/camera/2d_view.md), [3D projective camera via View3dConfig](viz/camera/3d_plane.md), [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md), [fixed screen-space axes + grid overlay in 2D](viz/camera/axes_overlay_2d.md), [2D fit-camera keeps the axes/grid undistorted](viz/camera/fit_2d.md), [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md), [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md), [a calibrated camera as a free orbit/pan/zoom view](viz/camera/pinhole_camera.md), [calibrated camera view (image) + default 3D overview](viz/camera/pinhole_overlay.md), [Toggle one scene between a 2D and 3D view with a checkbox](viz/camera/switch_2d_3d.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md)

- **capped cone** — [isolate the SDF arrowhead (capped cone) placement](viz/sdf/arrowhead.md)

- **Cayley-Bacharach** — [Q3 point tuples (1–7 points) in distinct colors](ga/quadric/point_tuples_demo.md)

- **cdn** — [Compare the three HTML delivery modes](viz/export/export_delivery.md)

- **cell editing** — [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md)

- **chaos** — [A chaotic double pendulum from nested VizGroups](viz/animation/double_pendulum.md)

- **checkbox** — [Toggle one scene between a 2D and 3D view with a checkbox](viz/camera/switch_2d_3d.md), [Controls styled from the extracted theme CSS files](viz/ui/controls/control_theming.md), [A custom theme with a full button/checkbox override](viz/ui/themes/custom_theme_override.md)

- **CheckboxView** — [Declarative controls drive a sphere](viz/ui/controls/controls_add_and_view.md)

- **Circle** — [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md)

- **classification** — [classify a noisy quadric within a tolerance](ga/quadric/tolerant_classification.md)

- **click** — [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md)

- **code generation** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **coefficients** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md)

- **column types** — [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md), [A TableView with a column-fed enum and a backend-fed enum](viz/ui/controls/table_enum_columns.md)

- **combine** — [per-object CSG combine modes](viz/sdf/booleans.md)

- **comparison** — [every solid object as a mesh next to its SDF twin](viz/sdf/mesh_vs_sdf_grid.md)

- **compilation** — [How pytanga builds C++ backends on the fly](binding_demo.md)

- **compile** — [Expression.compile() for fast repeated evaluation](ga/expression/compile_fastpath.md)

- **compose** — [Compose a detached scene subtree, then insert it](viz/scenes/compose_detached.md)

- **Composed** — [Combine multiple SdfGroups (nesting + merging)](viz/sdf/combine_groups.md), [Composed SDF objects + the primitive library](viz/sdf/composed.md)

- **composition** — [Bind a variable to a sub-expression (composition)](ga/expression/bind_subexpression.md)

- **cone** — [lift a 2D conic into a 3D cone through an apex](ga/quadric/cone_from_conic.md), [draw arbitrary quadrics via entities + GA translation](ga/quadric/general_quadric.md), [classify a noisy quadric within a tolerance](ga/quadric/tolerant_classification.md)

- **confirm** — [Demonstrates every banner/dialog kind](viz/ui/banners/banner_types.md), [Banners scoped to a named scene via VizSceneHandle](viz/ui/banners/scene_banner.md)

- **conformal** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md), [BladeMask named bases (auto display basis, composed names, with_basis)](ga/blade_mask/named_basis.md), [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md), [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md)

- **conic** — [lift a 2D conic into a 3D cone through an apex](ga/quadric/cone_from_conic.md), [reconstruct a conic from 5 points and rotate it with a slider](ga/quadric/conic_demo.md), [intersect two 2D conics (a point tuple)](ga/quadric/conic_intersection_demo.md), [fit a conic/quadric from points with the GA primitives](ga/quadric/fit_conic_quadric.md), [intersect two 3D quadrics (Perwass pencil)](ga/quadric/quadric_intersection_demo.md)

- **conic_from_points** — [reconstruct a conic from 5 points and rotate it with a slider](ga/quadric/conic_demo.md)

- **constraints** — [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md)

- **construction** — [Three ways to work with named basis blades](ga/basis/basis_usage.md)

- **context manager** — [Interactive Visualizer](viz/jupyter/interactive.md), [Two named scenes, each shown in its own browser tab](viz/scenes/multi_scene.md)

- **contraction** — [Expressions, variables, and DataArray bindings](expression_dataarray.md)

- **control group** — [Declarative control groups: overlay + 3D-anchored](viz/ui/controls/control_group_overlay.md), [Declarative control groups on a single-scene page](viz/ui/controls/control_group_single.md)

- **control update** — [Settable label and markdown panes in a vertical split](viz/ui/static/display_views.md)

- **controls** — [Showcase every interactive control in one app](viz/ui/controls/all_controls.md), [Controls styled from the extracted theme CSS files](viz/ui/controls/control_theming.md), [Declarative controls drive a sphere](viz/ui/controls/controls_add_and_view.md), [A file chooser with a backend-driven file browser](viz/ui/controls/file_chooser.md), [An editable tabular-data control driven by the backend](viz/ui/controls/table_data.md), [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md), [A TableView with a column-fed enum and a backend-fed enum](viz/ui/controls/table_enum_columns.md), [Table auto-save: JSON load/save + CSV export](viz/ui/controls/table_file.md), [Switch the viewer theme at runtime without a reload](viz/ui/themes/theme_switching.md)

- **CoordinateSystem** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [fixed screen-space axes + grid overlay in 2D](viz/camera/axes_overlay_2d.md), [annotations in a CoordinateSystem's data frame](viz/plotting/cs_annotations.md), [logarithmic plotting with CoordinateSystem](viz/plotting/log_plot.md), [2D plots across a split view, one stretch mode per pane](viz/plotting/multi_plot.md)

- **counting axis** — [Sum an AffineExpression over a batched variable](ga/expression/affine_counting_reduction.md)

- **cp** — [Named GA product functions over variables](ga/expression/named_products.md)

- **CSG** — [per-object CSG combine modes](viz/sdf/booleans.md), [SDF object groups with per-member CSG + independent animation](viz/sdf/group.md)

- **css** — [Controls styled from the extracted theme CSS files](viz/ui/controls/control_theming.md)

- **CSV** — [Table auto-save: JSON load/save + CSV export](viz/ui/controls/table_file.md)

- **Ctrl+C** — [Nested animation loops honoring Ctrl+C](viz/animation/nested_sweep.md)

- **cursor** — [Add and drag rectangles on an image via a toolbar](viz/image/rectangle_labeling.md)

- **curve** — [intersect two 3D quadrics (Perwass pencil)](ga/quadric/quadric_intersection_demo.md)

- **custom enum** — [A TableView with a column-fed enum and a backend-fed enum](viz/ui/controls/table_enum_columns.md)

- **custom intervals** — [Custom axes and grid as explicit scene objects](viz/plotting/axes_custom.md)

- **custom shader** — [Custom image shader that rotates RGB vectors](viz/image/custom_shader_rgb_rotate.md)

- **custom theme** — [Load a custom theme and edit it live](viz/ui/themes/custom_theme_autoreload.md), [A custom theme with a full button/checkbox override](viz/ui/themes/custom_theme_override.md)

- **Cylinder** — [the visualization-only Cylinder and Arc entities](viz/entities/viz_entities.md)

- **cylinder** — [Compose a detached scene subtree, then insert it](viz/scenes/compose_detached.md)

- **dark** — [Switch the viewer theme at runtime without a reload](viz/ui/themes/theme_switching.md)

- **DataArray** — [Expressions, variables, and DataArray bindings](expression_dataarray.md), [Sum an AffineExpression over a batched variable](ga/expression/affine_counting_reduction.md)

- **defaults** — [Global default styles and per-call overrides](viz/styling/custom_defaults.md)

- **degenerate** — [degenerate quadric (plane pair) analysis + rendering](ga/quadric/plane_pair_demo.md)

- **delivery** — [Compare the three HTML delivery modes](viz/export/export_delivery.md)

- **detached** — [Compose a detached scene subtree, then insert it](viz/scenes/compose_detached.md)

- **dialog** — [Demonstrates every banner/dialog kind](viz/ui/banners/banner_types.md), [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md), [A file-selection view, embedded and in a dialog box](viz/ui/dialogs/file_chooser_dialog.md)

- **Dilator** — [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md)

- **dimension** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md)

- **Direction** — [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md)

- **Disk** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **display** — [Interactive Visualizer](viz/jupyter/interactive.md)

- **double pendulum** — [A chaotic double pendulum from nested VizGroups](viz/animation/double_pendulum.md)

- **drag** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [Custom image shader that rotates RGB vectors](viz/image/custom_shader_rgb_rotate.md), [Add and drag rectangles on an image via a toolbar](viz/image/rectangle_labeling.md), [Demo: Drag a 3D point interactively with ActPoint](viz/interaction/act_point.md), [Demo: Drag TWO 3D points interactively with ActPoint](viz/interaction/act_point_two.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md), [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md)

- **dropdown** — [reconstruct a quadric from 9 points and rotate it](ga/quadric/quadric3d_demo.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md), [Showcase every interactive control in one app](viz/ui/controls/all_controls.md), [Four toolbars, one per alignment, stacked in a vertical split](viz/ui/controls/toolbar.md), [Menus: per-pane overlay, sub-menus, and sub-sub-menus](viz/ui/menus/menu_demo.md)

- **dtype** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md)

- **dual modulus** — [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md)

- **E3** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md), [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **easing** — [Keyframe timeline with fade-in and move](viz/animation/timeline.md)

- **einsum** — [multilinear AffineExpression.get_tensor()](ga/expression/quadratic_get_tensor.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **Ellipse** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **ellipsoid** — [reconstruct a quadric from 9 points and rotate it](ga/quadric/quadric3d_demo.md)

- **Ellipsoid** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **entities** — [All geometric entity types in one scene](viz/entities/all_entities.md), [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md), [the visualization-only Cylinder and Arc entities](viz/entities/viz_entities.md), [First vertical slice for the SDF viewer](viz/sdf/entities.md)

- **entity** — [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md)

- **enum** — [A TableView with a column-fed enum and a backend-fed enum](viz/ui/controls/table_enum_columns.md)

- **Euclidean** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md), [Project an N3 expression onto the Euclidean basis](ga/expression/project_onto_euclidean_n3.md)

- **explicit** — [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md)

- **export** — [Animated HTML export with JS playback engine](viz/export/animated.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md), [Compare the three HTML delivery modes](viz/export/export_delivery.md), [Presentation figure export with FigureStyle](viz/export/figure.md), [Self-contained HTML and glTF export](viz/export/html_export.md), [Programmatic PNG screenshot at custom resolution](viz/export/screenshot.md), [Export](viz/jupyter/export.md)

- **expression** — [Expressions, variables, and DataArray bindings](expression_dataarray.md)

- **expressions** — [Sum an AffineExpression over a batched variable](ga/expression/affine_counting_reduction.md), [Solve a single-linear-map AffineExpression](ga/expression/affine_linear_solve.md), [Bind a variable to a sub-expression (composition)](ga/expression/bind_subexpression.md), [Expression.compile() for fast repeated evaluation](ga/expression/compile_fastpath.md), [Multi-variable linear equations with Variables](ga/expression/equation_demo.md), [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md), [Named GA product functions over variables](ga/expression/named_products.md), [Polynomial (repeated-variable) expressions and affine sums](ga/expression/polynomial_demo.md), [Project an N3 expression onto the Euclidean basis](ga/expression/project_onto_euclidean_n3.md), [multilinear AffineExpression.get_tensor()](ga/expression/quadratic_get_tensor.md), [Re-key variables so independent expressions merge](ga/expression/rename_unify_variables.md), [Solve the general multivector equation A X = B with expressions](ga/expression/solve_ax_b.md), [get_tensor() (raw MVTensor) + get_array() (named bases)](ga/expression/tensor_named_basis.md), [Apply a fixed rotor to points with a Variable-backed expression](ga/expression/variable_rotor.md), [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md)

- **figure** — [Presentation figure export with FigureStyle](viz/export/figure.md), [Export](viz/jupyter/export.md)

- **FigureStyle** — [Presentation figure export with FigureStyle](viz/export/figure.md)

- **file browser** — [A file chooser with a backend-driven file browser](viz/ui/controls/file_chooser.md)

- **file chooser** — [A file chooser with a backend-driven file browser](viz/ui/controls/file_chooser.md), [A file-selection view, embedded and in a dialog box](viz/ui/dialogs/file_chooser_dialog.md)

- **file dialog** — [A menu bar with a File → Open… file dialog](viz/ui/menus/file_open_menu.md)

- **FileChooserDialog** — [A file-selection view, embedded and in a dialog box](viz/ui/dialogs/file_chooser_dialog.md), [A menu bar with a File → Open… file dialog](viz/ui/menus/file_open_menu.md)

- **FileChooserView** — [A file-selection view, embedded and in a dialog box](viz/ui/dialogs/file_chooser_dialog.md)

- **first slice** — [First vertical slice for the SDF viewer](viz/sdf/entities.md)

- **fit camera** — [2D fit-camera keeps the axes/grid undistorted](viz/camera/fit_2d.md)

- **fit_view2d** — [2D plots across a split view, one stretch mode per pane](viz/plotting/multi_plot.md)

- **fitting** — [fit a conic/quadric from points with the GA primitives](ga/quadric/fit_conic_quadric.md)

- **fixed modulus** — [Integer GA with a single modulus (Path C)](ga/algebra/modulus_algebra_single.md)

- **flex** — [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md), [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md)

- **fold** — [Group view chrome: leading icon, icon-only, borderless fold](viz/ui/controls/group_view_icons.md)

- **fr** — [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md)

- **frame streaming** — [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md)

- **frustum** — [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md), [a calibrated camera as a free orbit/pan/zoom view](viz/camera/pinhole_camera.md), [calibrated camera view (image) + default 3D overview](viz/camera/pinhole_overlay.md)

- **G(3,0)** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md)

- **G(3,1)** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md)

- **G(4,0)** — [Projective 3D geometric algebra  G(4, 0)](ga/basis/base_p3_demo.md)

- **G(5,0b10000)** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md)

- **gap** — [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md)

- **general solve** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_01.md), [Core solver API: inverse and general solve](ga/numerics/solver_basics_02.md)

- **geometric algebra** — [Expressions, variables, and DataArray bindings](expression_dataarray.md)

- **geometric product** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md)

- **geometry** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md)

- **Geometry** — [classify a noisy quadric within a tolerance](ga/quadric/tolerant_classification.md)

- **get_array** — [multilinear AffineExpression.get_tensor()](ga/expression/quadratic_get_tensor.md), [get_tensor() (raw MVTensor) + get_array() (named bases)](ga/expression/tensor_named_basis.md)

- **get_tensor** — [multilinear AffineExpression.get_tensor()](ga/expression/quadratic_get_tensor.md), [get_tensor() (raw MVTensor) + get_array() (named bases)](ga/expression/tensor_named_basis.md)

- **GLSL** — [Custom image shader that rotates RGB vectors](viz/image/custom_shader_rgb_rotate.md)

- **glTF** — [Self-contained HTML and glTF export](viz/export/html_export.md), [Export](viz/jupyter/export.md)

- **gp** — [Named GA product functions over variables](ga/expression/named_products.md)

- **gradient** — [Moving point with a color-gradient trail](viz/animation/point_path_trail.md)

- **gravity** — [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md)

- **Grid** — [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md), [Custom axes and grid as explicit scene objects](viz/plotting/axes_custom.md)

- **grid** — [fixed screen-space axes + grid overlay in 2D](viz/camera/axes_overlay_2d.md)

- **group** — [SDF object groups with per-member CSG + independent animation](viz/sdf/group.md)

- **group view** — [Group view chrome: leading icon, icon-only, borderless fold](viz/ui/controls/group_view_icons.md)

- **GroupView** — [Declarative control groups: overlay + 3D-anchored](viz/ui/controls/control_group_overlay.md), [Declarative control groups on a single-scene page](viz/ui/controls/control_group_single.md), [Declarative controls drive a sphere](viz/ui/controls/controls_add_and_view.md)

- **Gunn/Dorst** — [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md)

- **heavy work** — [Slider that triggers a blocking computation on release](viz/ui/banners/heavy_work.md)

- **hierarchy** — [Demonstrate nested VizGroup hierarchies](viz/scenes/nested_groups.md)

- **history** — [A live, auto-scrolling two-column log in a split pane](viz/ui/static/log_view.md)

- **homogeneous** — [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md)

- **HTML** — [Animated HTML export with JS playback engine](viz/export/animated.md), [2D animated HTML export with a moving camera](viz/export/animated_camera_2d.md), [3D animated HTML export with a moving camera](viz/export/animated_camera_3d.md), [Compare the three HTML delivery modes](viz/export/export_delivery.md), [Self-contained HTML and glTF export](viz/export/html_export.md), [Export](viz/jupyter/export.md)

- **hyperboloid** — [draw arbitrary quadrics via entities + GA translation](ga/quadric/general_quadric.md)

- **icon** — [Add and drag rectangles on an image via a toolbar](viz/image/rectangle_labeling.md), [Group view chrome: leading icon, icon-only, borderless fold](viz/ui/controls/group_view_icons.md), [Four toolbars, one per alignment, stacked in a vertical split](viz/ui/controls/toolbar.md)

- **icon_only** — [Controls styled from the extracted theme CSS files](viz/ui/controls/control_theming.md), [Group view chrome: leading icon, icon-only, borderless fold](viz/ui/controls/group_view_icons.md)

- **image** — [Custom image shader that rotates RGB vectors](viz/image/custom_shader_rgb_rotate.md), [Display a numpy image and draw pixel-coordinate overlays](viz/image/image_canvas.md), [Add and drag rectangles on an image via a toolbar](viz/image/rectangle_labeling.md)

- **image background** — [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md), [calibrated camera view (image) + default 3D overview](viz/camera/pinhole_overlay.md)

- **ImageCanvas** — [Custom image shader that rotates RGB vectors](viz/image/custom_shader_rgb_rotate.md), [Display a numpy image and draw pixel-coordinate overlays](viz/image/image_canvas.md)

- **initialization** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md)

- **inline** — [Compare the three HTML delivery modes](viz/export/export_delivery.md)

- **integer** — [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md), [Integer GA with a single modulus (Path C)](ga/algebra/modulus_algebra_single.md)

- **interaction** — [Demo: Drag a 3D point interactively with ActPoint](viz/interaction/act_point.md), [Demo: Drag TWO 3D points interactively with ActPoint](viz/interaction/act_point_two.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md), [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md)

- **interactive** — [Interactive Visualizer](viz/jupyter/interactive.md)

- **intersection** — [intersect two 2D conics (a point tuple)](ga/quadric/conic_intersection_demo.md), [intersect two 3D quadrics (Perwass pencil)](ga/quadric/quadric_intersection_demo.md)

- **inv** — [Solve a single-linear-map AffineExpression](ga/expression/affine_linear_solve.md)

- **inverse** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_01.md), [Core solver API: inverse and general solve](ga/numerics/solver_basics_02.md)

- **Inversion** — [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md)

- **IPNS** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md)

- **join** — [Q3 point tuples (1–7 points) in distinct colors](ga/quadric/point_tuples_demo.md), [reconstruct a quadric from 9 points and rotate it](ga/quadric/quadric3d_demo.md), [reconstruct a quadric from 9 points and ray-render it](ga/quadric/quadric3d_raycast.md)

- **JSON** — [Table auto-save: JSON load/save + CSV export](viz/ui/controls/table_file.md)

- **justify** — [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md)

- **KaTeX** — [Demo: Texture labels on spheres using plain text and KaTeX formulas](viz/labels/texture_sphere.md), [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md), [Settable label and markdown panes in a vertical split](viz/ui/static/display_views.md)

- **keyboard navigation** — [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md)

- **keyframe** — [Keyframe timeline with fade-in and move](viz/animation/timeline.md)

- **label** — [Settable label and markdown panes in a vertical split](viz/ui/static/display_views.md)

- **labels** — [Labels with custom styling, dynamic update, and removal](viz/labels/basic.md)

- **LabelStyle** — [Labels with custom styling, dynamic update, and removal](viz/labels/basic.md)

- **LaTeX** — [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md)

- **layout** — [Declarative control groups: overlay + 3D-anchored](viz/ui/controls/control_group_overlay.md), [Four toolbars, one per alignment, stacked in a vertical split](viz/ui/controls/toolbar.md), [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md), [Three scenes side-by-side in one horizontal split](viz/ui/layout/multi_split.md), [A single page showing multiple scenes in split panes](viz/ui/layout/split_view.md), [Menus: per-pane overlay, sub-menus, and sub-sub-menus](viz/ui/menus/menu_demo.md), [Settable label and markdown panes in a vertical split](viz/ui/static/display_views.md), [A live, auto-scrolling two-column log in a split pane](viz/ui/static/log_view.md)

- **least-norm** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md)

- **least-squares** — [Solve a single-linear-map AffineExpression](ga/expression/affine_linear_solve.md), [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md), [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md), [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Best-fit rotor from point correspondences](ga/numerics/solver_rotor_estimation.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md)

- **lift** — [lift a 2D conic into a 3D cone through an apex](ga/quadric/cone_from_conic.md)

- **light** — [Animate a directional light around a sphere](viz/sdf/light_animation.md), [A custom theme with a full button/checkbox override](viz/ui/themes/custom_theme_override.md), [Switch the viewer theme at runtime without a reload](viz/ui/themes/theme_switching.md)

- **Line** — [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [All geometric entity types in one scene](viz/entities/all_entities.md)

- **line fitting** — [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md), [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md)

- **linear equations** — [Multi-variable linear equations with Variables](ga/expression/equation_demo.md)

- **linear system** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_01.md)

- **live plot** — [a swinging pendulum with a live angle-vs-time plot](viz/plotting/pendulum_plot.md)

- **lock** — [calibrated camera view (image) + default 3D overview](viz/camera/pinhole_overlay.md)

- **log** — [A live, auto-scrolling two-column log in a split pane](viz/ui/static/log_view.md)

- **log plot** — [logarithmic plotting with CoordinateSystem](viz/plotting/log_plot.md)

- **low-level** — [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md)

- **Markdown** — [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md)

- **markdown** — [Settable label and markdown panes in a vertical split](viz/ui/static/display_views.md)

- **menu** — [A menu bar with a File → Open… file dialog](viz/ui/menus/file_open_menu.md), [Menus: per-pane overlay, sub-menus, and sub-sub-menus](viz/ui/menus/menu_demo.md)

- **menu bar** — [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md), [A menu bar with a File → Open… file dialog](viz/ui/menus/file_open_menu.md)

- **merge** — [Re-key variables so independent expressions merge](ga/expression/rename_unify_variables.md), [Combine multiple SdfGroups (nesting + merging)](viz/sdf/combine_groups.md)

- **mesh** — [every solid object as a mesh next to its SDF twin](viz/sdf/mesh_vs_sdf_grid.md)

- **meshes** — [Mix standard meshes with SDF-styled objects](viz/sdf/objects.md)

- **modal** — [Slider that triggers a blocking computation on release](viz/ui/banners/heavy_work.md), [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md)

- **modes** — [Auto-fit, explicit, and partial camera modes](viz/camera/modes.md)

- **modulus** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md), [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md), [Integer GA with a single modulus (Path C)](ga/algebra/modulus_algebra_single.md)

- **Motor** — [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md), [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md), [Drive a VizGroup transform from a BasisN3 Motor](viz/scenes/motor_group_transform.md)

- **multi-pane** — [Three scenes side-by-side in one horizontal split](viz/ui/layout/multi_split.md)

- **multi-scene** — [Two named scenes, each shown in its own browser tab](viz/scenes/multi_scene.md)

- **multilinear** — [multilinear AffineExpression.get_tensor()](ga/expression/quadratic_get_tensor.md)

- **multivector** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md)

- **multivector equation** — [Solve the general multivector equation A X = B with expressions](ga/expression/solve_ax_b.md)

- **MV** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md)

- **MVTensor** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md)

- **N3** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md), [BladeMask named bases (auto display basis, composed names, with_basis)](ga/blade_mask/named_basis.md), [Expression.compile() for fast repeated evaluation](ga/expression/compile_fastpath.md), [Project an N3 expression onto the Euclidean basis](ga/expression/project_onto_euclidean_n3.md), [multilinear AffineExpression.get_tensor()](ga/expression/quadratic_get_tensor.md), [get_tensor() (raw MVTensor) + get_array() (named bases)](ga/expression/tensor_named_basis.md), [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md), [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md)

- **named blades** — [Euclidean 3D geometric algebra  G(3, 0)](ga/basis/base_e3_demo.md), [Three ways to work with named basis blades](ga/basis/basis_usage.md)

- **nested** — [Demonstrate nested VizGroup hierarchies](viz/scenes/nested_groups.md)

- **nested loops** — [Nested animation loops honoring Ctrl+C](viz/animation/nested_sweep.md)

- **nesting** — [Combine multiple SdfGroups (nesting + merging)](viz/sdf/combine_groups.md)

- **notebook** — [Animation](viz/jupyter/animation.md), [Export](viz/jupyter/export.md), [Interactive Visualizer](viz/jupyter/interactive.md)

- **NTRU** — [Integer GA with two different moduli (NTRU style)](ga/algebra/modulus_algebra_multi.md)

- **null vector** — [Null / conformal 3D algebra  G(5, 0b10000)](ga/basis/base_n3_demo.md), [Projective GA  (PGA 3D)](ga/basis/base_pga3_demo.md)

- **nullity** — [fit a conic/quadric from points with the GA primitives](ga/quadric/fit_conic_quadric.md)

- **object model** — [the unified SDF object model in the standard viewer](viz/sdf/object_model.md)

- **offline** — [Compare the three HTML delivery modes](viz/export/export_delivery.md)

- **on_close** — [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md)

- **on_release** — [Slider that triggers a blocking computation on release](viz/ui/banners/heavy_work.md)

- **OpenCV** — [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md)

- **operators** — [The MV class: initialization, operators, and named methods](ga/algebra/mv_demo.md)

- **OPNS** — [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md)

- **orbit** — [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md)

- **orthographic** — [2D orthographic view via View2DConfig](viz/camera/2d_view.md), [2D fit-camera keeps the axes/grid undistorted](viz/camera/fit_2d.md)

- **outer product** — [lift a 2D conic into a 3D cone through an apex](ga/quadric/cone_from_conic.md), [fit a conic/quadric from points with the GA primitives](ga/quadric/fit_conic_quadric.md)

- **overlay** — [fixed screen-space axes + grid overlay in 2D](viz/camera/axes_overlay_2d.md), [Display a numpy image and draw pixel-coordinate overlays](viz/image/image_canvas.md), [2D plots across a split view, one stretch mode per pane](viz/plotting/multi_plot.md), [Declarative control groups: overlay + 3D-anchored](viz/ui/controls/control_group_overlay.md), [Declarative control groups on a single-scene page](viz/ui/controls/control_group_single.md), [Group view chrome: leading icon, icon-only, borderless fold](viz/ui/controls/group_view_icons.md), [Menus: per-pane overlay, sub-menus, and sub-sub-menus](viz/ui/menus/menu_demo.md)

- **override** — [Load a custom theme and edit it live](viz/ui/themes/custom_theme_autoreload.md), [A custom theme with a full button/checkbox override](viz/ui/themes/custom_theme_override.md)

- **overrides** — [Global default styles and per-call overrides](viz/styling/custom_defaults.md)

- **P2** — [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md)

- **P3** — [Projective 3D geometric algebra  G(4, 0)](ga/basis/base_p3_demo.md), [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md), [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md)

- **panes** — [2D plots across a split view, one stretch mode per pane](viz/plotting/multi_plot.md), [Three scenes side-by-side in one horizontal split](viz/ui/layout/multi_split.md), [A single page showing multiple scenes in split panes](viz/ui/layout/split_view.md)

- **paraboloid** — [draw arbitrary quadrics via entities + GA translation](ga/quadric/general_quadric.md)

- **parent_id** — [Declarative control groups: overlay + 3D-anchored](viz/ui/controls/control_group_overlay.md), [Declarative control groups on a single-scene page](viz/ui/controls/control_group_single.md)

- **PartialDisk** — [the Disk, PartialDisk, Box, Ellipsoid, Ellipse, and](viz/entities/extra_entities.md)

- **pencil** — [intersect two 2D conics (a point tuple)](ga/quadric/conic_intersection_demo.md), [intersect two 3D quadrics (Perwass pencil)](ga/quadric/quadric_intersection_demo.md)

- **pendulum** — [a swinging pendulum with a live angle-vs-time plot](viz/plotting/pendulum_plot.md)

- **performance** — [Expression.compile() for fast repeated evaluation](ga/expression/compile_fastpath.md)

- **persistence** — [Table auto-save: JSON load/save + CSV export](viz/ui/controls/table_file.md)

- **PGA3** — [Projective GA  (PGA 3D)](ga/basis/base_pga3_demo.md), [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md), [MV input from PGA3 and N3, OPNS vs IPNS](viz/entities/multivector.md)

- **pinhole** — [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md), [a calibrated camera as a free orbit/pan/zoom view](viz/camera/pinhole_camera.md), [calibrated camera view (image) + default 3D overview](viz/camera/pinhole_overlay.md)

- **pixels** — [Display a numpy image and draw pixel-coordinate overlays](viz/image/image_canvas.md)

- **Plane** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [All geometric entity types in one scene](viz/entities/all_entities.md)

- **plane** — [Demo: Texture labels on planes with different align modes](viz/labels/texture_plane.md)

- **plane pair** — [degenerate quadric (plane pair) analysis + rendering](ga/quadric/plane_pair_demo.md), [intersect two 3D quadrics (Perwass pencil)](ga/quadric/quadric_intersection_demo.md)

- **plane-based** — [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md)

- **playback** — [Animated HTML export with JS playback engine](viz/export/animated.md)

- **plot** — [Toggle one scene between a 2D and 3D view with a checkbox](viz/camera/switch_2d_3d.md)

- **plotting** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [Custom axes and grid as explicit scene objects](viz/plotting/axes_custom.md), [annotations in a CoordinateSystem's data frame](viz/plotting/cs_annotations.md), [logarithmic plotting with CoordinateSystem](viz/plotting/log_plot.md), [2D plots across a split view, one stretch mode per pane](viz/plotting/multi_plot.md), [a swinging pendulum with a live angle-vs-time plot](viz/plotting/pendulum_plot.md), [a plot on a tilted background plane in 3D](viz/plotting/plot_3d.md)

- **PNG** — [Programmatic PNG screenshot at custom resolution](viz/export/screenshot.md)

- **Point** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md), [Frame-by-frame animation at ~60 FPS](viz/animation/orbit.md), [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md), [All geometric entity types in one scene](viz/entities/all_entities.md)

- **point** — [Demo: Drag a 3D point interactively with ActPoint](viz/interaction/act_point.md), [Demo: Drag a 3D point interactively with the mouse](viz/interaction/drag_point.md)

- **point correspondences** — [Best-fit rotor from point correspondences](ga/numerics/solver_rotor_estimation.md)

- **Point Pair** — [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md)

- **point tuple** — [Q3 point tuples (1–7 points) in distinct colors](ga/quadric/point_tuples_demo.md)

- **point-line matching** — [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md)

- **PointPath** — [Moving point with a color-gradient trail](viz/animation/point_path_trail.md)

- **points** — [Apply a fixed rotor to points with a Variable-backed expression](ga/expression/variable_rotor.md), [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md)

- **PointSet** — [intersect two 2D conics (a point tuple)](ga/quadric/conic_intersection_demo.md), [Q3 point tuples (1–7 points) in distinct colors](ga/quadric/point_tuples_demo.md)

- **polarity** — [per-object CSG combine modes](viz/sdf/booleans.md)

- **polynomial** — [Polynomial (repeated-variable) expressions and affine sums](ga/expression/polynomial_demo.md)

- **presentation** — [Presentation figure export with FigureStyle](viz/export/figure.md)

- **primitive library** — [Composed SDF objects + the primitive library](viz/sdf/composed.md)

- **product tensor** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **project_onto** — [Project an N3 expression onto the Euclidean basis](ga/expression/project_onto_euclidean_n3.md)

- **projective** — [Projective 3D geometric algebra  G(4, 0)](ga/basis/base_p3_demo.md), [Projective 3D geometry: Points, Directions, Lines, Planes](ga/geometry/p3_entities.md)

- **projective geometric algebra** — [Projective GA  (PGA 3D)](ga/basis/base_pga3_demo.md)

- **Q2** — [intersect two 2D conics (a point tuple)](ga/quadric/conic_intersection_demo.md)

- **Q3** — [degenerate quadric (plane pair) analysis + rendering](ga/quadric/plane_pair_demo.md), [Q3 point tuples (1–7 points) in distinct colors](ga/quadric/point_tuples_demo.md), [intersect two 3D quadrics (Perwass pencil)](ga/quadric/quadric_intersection_demo.md)

- **quadratic** — [multilinear AffineExpression.get_tensor()](ga/expression/quadratic_get_tensor.md)

- **quadric** — [lift a 2D conic into a 3D cone through an apex](ga/quadric/cone_from_conic.md), [reconstruct a conic from 5 points and rotate it with a slider](ga/quadric/conic_demo.md), [intersect two 2D conics (a point tuple)](ga/quadric/conic_intersection_demo.md), [fit a conic/quadric from points with the GA primitives](ga/quadric/fit_conic_quadric.md), [draw arbitrary quadrics via entities + GA translation](ga/quadric/general_quadric.md), [degenerate quadric (plane pair) analysis + rendering](ga/quadric/plane_pair_demo.md), [Q3 point tuples (1–7 points) in distinct colors](ga/quadric/point_tuples_demo.md), [reconstruct a quadric from 9 points and rotate it](ga/quadric/quadric3d_demo.md), [reconstruct a quadric from 9 points and ray-render it](ga/quadric/quadric3d_raycast.md), [intersect two 3D quadrics (Perwass pencil)](ga/quadric/quadric_intersection_demo.md), [classify a noisy quadric within a tolerance](ga/quadric/tolerant_classification.md)

- **Quadric3D** — [draw arbitrary quadrics via entities + GA translation](ga/quadric/general_quadric.md)

- **quadric3d** — [reconstruct a quadric from 9 points and rotate it](ga/quadric/quadric3d_demo.md)

- **quadric_from_points** — [reconstruct a quadric from 9 points and ray-render it](ga/quadric/quadric3d_raycast.md)

- **ray** — [draw arbitrary quadrics via entities + GA translation](ga/quadric/general_quadric.md), [reconstruct a quadric from 9 points and ray-render it](ga/quadric/quadric3d_raycast.md)

- **rc** — [Named GA product functions over variables](ga/expression/named_products.md)

- **re-run** — [Interactive Visualizer](viz/jupyter/interactive.md)

- **rectangle** — [Display a numpy image and draw pixel-coordinate overlays](viz/image/image_canvas.md), [Add and drag rectangles on an image via a toolbar](viz/image/rectangle_labeling.md)

- **Rectangle2D** — [Display a numpy image and draw pixel-coordinate overlays](viz/image/image_canvas.md)

- **redo** — [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md)

- **refine** — [reconstruct a conic from 5 points and rotate it with a slider](ga/quadric/conic_demo.md), [degenerate quadric (plane pair) analysis + rendering](ga/quadric/plane_pair_demo.md), [reconstruct a quadric from 9 points and ray-render it](ga/quadric/quadric3d_raycast.md), [classify a noisy quadric within a tolerance](ga/quadric/tolerant_classification.md)

- **Reflection** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md)

- **register_theme** — [Load a custom theme and edit it live](viz/ui/themes/custom_theme_autoreload.md)

- **remove** — [Labels with custom styling, dynamic update, and removal](viz/labels/basic.md)

- **remove_dialog** — [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md)

- **rename_var** — [Re-key variables so independent expressions merge](ga/expression/rename_unify_variables.md)

- **repeated variables** — [Polynomial (repeated-variable) expressions and affine sums](ga/expression/polynomial_demo.md)

- **residual** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_02.md)

- **RGB** — [Custom image shader that rotates RGB vectors](viz/image/custom_shader_rgb_rotate.md)

- **rotation** — [Custom image shader that rotates RGB vectors](viz/image/custom_shader_rgb_rotate.md)

- **rotor** — [Bind a variable to a sub-expression (composition)](ga/expression/bind_subexpression.md), [Expression.compile() for fast repeated evaluation](ga/expression/compile_fastpath.md), [Apply a fixed rotor to points with a Variable-backed expression](ga/expression/variable_rotor.md), [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md), [reconstruct a conic from 5 points and rotate it with a slider](ga/quadric/conic_demo.md), [reconstruct a quadric from 9 points and rotate it](ga/quadric/quadric3d_demo.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **Rotor** — [Euclidean 3D geometry: Points, Planes, Reflections, Rotors](ga/geometry/e3_entities.md), [Full conformal (N3) operators: Rotors, Motors, Inversions](ga/geometry/n3_operators.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md)

- **rotor estimation** — [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Best-fit rotor from point correspondences](ga/numerics/solver_rotor_estimation.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md)

- **runtime** — [Switch the viewer theme at runtime without a reload](viz/ui/themes/theme_switching.md)

- **sandwich** — [Expression.compile() for fast repeated evaluation](ga/expression/compile_fastpath.md)

- **scene** — [Banners scoped to a named scene via VizSceneHandle](viz/ui/banners/scene_banner.md), [Declarative controls drive a sphere](viz/ui/controls/controls_add_and_view.md)

- **scene graph** — [Compose a detached scene subtree, then insert it](viz/scenes/compose_detached.md), [Drive a VizGroup transform from a BasisN3 Motor](viz/scenes/motor_group_transform.md), [Demonstrate VizGroup + direct transforms](viz/scenes/scene_graph.md)

- **scenes** — [Two named scenes, each shown in its own browser tab](viz/scenes/multi_scene.md), [Demonstrate nested VizGroup hierarchies](viz/scenes/nested_groups.md), [Demonstrate VizGroup + direct transforms](viz/scenes/scene_graph.md)

- **screenshot** — [Programmatic PNG screenshot at custom resolution](viz/export/screenshot.md)

- **SDF** — [isolate the SDF arrowhead (capped cone) placement](viz/sdf/arrowhead.md), [per-object CSG combine modes](viz/sdf/booleans.md), [Combine multiple SdfGroups (nesting + merging)](viz/sdf/combine_groups.md), [Composed SDF objects + the primitive library](viz/sdf/composed.md), [First vertical slice for the SDF viewer](viz/sdf/entities.md), [SDF object groups with per-member CSG + independent animation](viz/sdf/group.md), [Animate a directional light around a sphere](viz/sdf/light_animation.md), [every solid object as a mesh next to its SDF twin](viz/sdf/mesh_vs_sdf_grid.md), [the unified SDF object model in the standard viewer](viz/sdf/object_model.md), [Mix standard meshes with SDF-styled objects](viz/sdf/objects.md), [Smooth CSG in the standard viewer](viz/sdf/smooth_csg.md)

- **SdfGroup** — [Combine multiple SdfGroups (nesting + merging)](viz/sdf/combine_groups.md)

- **separator** — [Four toolbars, one per alignment, stacked in a vertical split](viz/ui/controls/toolbar.md)

- **set_default_color** — [Global default styles and per-call overrides](viz/styling/custom_defaults.md)

- **set_theme** — [Switch the viewer theme at runtime without a reload](viz/ui/themes/theme_switching.md)

- **shader** — [Display a numpy image and draw pixel-coordinate overlays](viz/image/image_canvas.md)

- **show** — [Interactive Visualizer](viz/jupyter/interactive.md)

- **show_dialog** — [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md), [A file-selection view, embedded and in a dialog box](viz/ui/dialogs/file_chooser_dialog.md)

- **signature** — [Creating and configuring an Algebra](ga/algebra/algebra_demo.md)

- **simulation** — [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md)

- **single scene** — [Declarative control groups on a single-scene page](viz/ui/controls/control_group_single.md)

- **singleton** — [Interactive Visualizer](viz/jupyter/interactive.md)

- **singular** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md)

- **Size** — [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md), [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md)

- **sizing** — [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md)

- **slider** — [reconstruct a conic from 5 points and rotate it with a slider](ga/quadric/conic_demo.md), [reconstruct a quadric from 9 points and rotate it](ga/quadric/quadric3d_demo.md), [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md), [Slider that triggers a blocking computation on release](viz/ui/banners/heavy_work.md), [Showcase every interactive control in one app](viz/ui/controls/all_controls.md), [Controls styled from the extracted theme CSS files](viz/ui/controls/control_theming.md), [Four toolbars, one per alignment, stacked in a vertical split](viz/ui/controls/toolbar.md)

- **SliderView** — [Declarative controls drive a sphere](viz/ui/controls/controls_add_and_view.md)

- **smooth CSG** — [Smooth CSG in the standard viewer](viz/sdf/smooth_csg.md)

- **smooth_intersection** — [Smooth CSG in the standard viewer](viz/sdf/smooth_csg.md)

- **smooth_union** — [Smooth CSG in the standard viewer](viz/sdf/smooth_csg.md)

- **smoothness** — [Smooth CSG in the standard viewer](viz/sdf/smooth_csg.md)

- **snapshot** — [Self-contained HTML and glTF export](viz/export/html_export.md), [Export](viz/jupyter/export.md)

- **solve** — [Solve a single-linear-map AffineExpression](ga/expression/affine_linear_solve.md), [Solve the general multivector equation A X = B with expressions](ga/expression/solve_ax_b.md)

- **solve_lsq** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md)

- **solver** — [Core solver API: inverse and general solve](ga/numerics/solver_basics_01.md), [Core solver API: inverse and general solve](ga/numerics/solver_basics_02.md), [Core solver API: inverse and general solve](ga/numerics/solver_basics_03.md), [Least-squares homogeneous line fitting in P2](ga/numerics/solver_line_fitting_p2.md), [Recover a rotor from 3D point ↔ projection-ray matches](ga/numerics/solver_point_line_p3.md), [Best-fit rotor from point correspondences](ga/numerics/solver_rotor_estimation.md)

- **sp** — [Named GA product functions over variables](ga/expression/named_products.md)

- **space_dim** — [Toggle one scene between a 2D and 3D view with a checkbox](viz/camera/switch_2d_3d.md)

- **Sphere** — [Full conformal (N3) entities: Spheres, Circles, Point Pairs](ga/geometry/n3_entities.md), [All geometric entity types in one scene](viz/entities/all_entities.md)

- **sphere** — [Demo: Texture labels on spheres using plain text and KaTeX formulas](viz/labels/texture_sphere.md), [Animate a directional light around a sphere](viz/sdf/light_animation.md)

- **spheres** — [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md)

- **split view** — [VisualizerApp with a sin/cos split view and draggable points](viz/app/split_view_app.md), [a real calibrated image (BOP T-LESS) + 3D overview](viz/camera/pinhole_calibrated.md), [a calibrated camera as a free orbit/pan/zoom view](viz/camera/pinhole_camera.md), [calibrated camera view (image) + default 3D overview](viz/camera/pinhole_overlay.md), [Add and drag rectangles on an image via a toolbar](viz/image/rectangle_labeling.md), [2D plots across a split view, one stretch mode per pane](viz/plotting/multi_plot.md), [An editable data table beside a 3D scene](viz/ui/controls/table_split.md), [Four toolbars, one per alignment, stacked in a vertical split](viz/ui/controls/toolbar.md), [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md), [Three scenes side-by-side in one horizontal split](viz/ui/layout/multi_split.md), [A single page showing multiple scenes in split panes](viz/ui/layout/split_view.md), [Settable label and markdown panes in a vertical split](viz/ui/static/display_views.md), [A live, auto-scrolling two-column log in a split pane](viz/ui/static/log_view.md)

- **stack view** — [A tour of StackView/SplitView spacing, alignment, and flex](viz/ui/layout/layout_sizing.md)

- **StackView** — [A titled dialog whose body holds view-based controls](viz/ui/dialogs/dialog_demo.md)

- **standard viewer** — [the unified SDF object model in the standard viewer](viz/sdf/object_model.md)

- **streaming** — [A live, auto-scrolling two-column log in a split pane](viz/ui/static/log_view.md)

- **stretch** — [2D plots across a split view, one stretch mode per pane](viz/plotting/multi_plot.md)

- **styled objects** — [Mix standard meshes with SDF-styled objects](viz/sdf/objects.md)

- **styling** — [Global default styles and per-call overrides](viz/styling/custom_defaults.md)

- **sub-expression** — [Bind a variable to a sub-expression (composition)](ga/expression/bind_subexpression.md)

- **sub-menu** — [Menus: per-pane overlay, sub-menus, and sub-sub-menus](viz/ui/menus/menu_demo.md)

- **sub-sub-menu** — [Menus: per-pane overlay, sub-menus, and sub-sub-menus](viz/ui/menus/menu_demo.md)

- **submenu** — [A menu bar with a File → Open… file dialog](viz/ui/menus/file_open_menu.md)

- **SVD** — [fit a conic/quadric from points with the GA primitives](ga/quadric/fit_conic_quadric.md)

- **sweep** — [Nested animation loops honoring Ctrl+C](viz/animation/nested_sweep.md)

- **switch view** — [Toggle one scene between a 2D and 3D view with a checkbox](viz/camera/switch_2d_3d.md)

- **table** — [An editable tabular-data control driven by the backend](viz/ui/controls/table_data.md), [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md), [A TableView with a column-fed enum and a backend-fed enum](viz/ui/controls/table_enum_columns.md), [Table auto-save: JSON load/save + CSV export](viz/ui/controls/table_file.md), [An editable data table beside a 3D scene](viz/ui/controls/table_split.md)

- **TableView** — [An editable tabular-data control driven by the backend](viz/ui/controls/table_data.md), [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md), [A TableView with a column-fed enum and a backend-fed enum](viz/ui/controls/table_enum_columns.md), [Table auto-save: JSON load/save + CSV export](viz/ui/controls/table_file.md), [An editable data table beside a 3D scene](viz/ui/controls/table_split.md)

- **tabs** — [Two named scenes, each shown in its own browser tab](viz/scenes/multi_scene.md)

- **tabular data** — [An editable tabular-data control driven by the backend](viz/ui/controls/table_data.md), [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md), [A TableView with a column-fed enum and a backend-fed enum](viz/ui/controls/table_enum_columns.md), [Table auto-save: JSON load/save + CSV export](viz/ui/controls/table_file.md), [An editable data table beside a 3D scene](viz/ui/controls/table_split.md)

- **tensor** — [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/basics_02.md), [Recover a rotor from point ↔ projection-ray matches](ga/tensor/rotor-point-on-ray_01.md), [Product tensor basics — compute the geometric product *via* tensor contraction](ga/tensor/rotor_01.md)

- **texture labels** — [Demo: Texture labels on planes with different align modes](viz/labels/texture_plane.md), [Demo: Texture labels on spheres using plain text and KaTeX formulas](viz/labels/texture_sphere.md)

- **theme** — [Controls styled from the extracted theme CSS files](viz/ui/controls/control_theming.md), [Load a custom theme and edit it live](viz/ui/themes/custom_theme_autoreload.md), [A custom theme with a full button/checkbox override](viz/ui/themes/custom_theme_override.md), [Switch the viewer theme at runtime without a reload](viz/ui/themes/theme_switching.md)

- **theme switching** — [A custom theme with a full button/checkbox override](viz/ui/themes/custom_theme_override.md)

- **themes** — [Load a custom theme and edit it live](viz/ui/themes/custom_theme_autoreload.md)

- **tilted plane** — [a plot on a tilted background plane in 3D](viz/plotting/plot_3d.md)

- **timeline** — [Keyframe timeline with fade-in and move](viz/animation/timeline.md)

- **title** — [Title overlay and Markdown + LaTeX annotation](viz/labels/title_annotation.md)

- **tokens** — [Load a custom theme and edit it live](viz/ui/themes/custom_theme_autoreload.md)

- **tolerance** — [classify a noisy quadric within a tolerance](ga/quadric/tolerant_classification.md)

- **toolbar** — [Add and drag rectangles on an image via a toolbar](viz/image/rectangle_labeling.md), [Four toolbars, one per alignment, stacked in a vertical split](viz/ui/controls/toolbar.md)

- **trail** — [Moving point with a color-gradient trail](viz/animation/point_path_trail.md)

- **Transform** — [Drive a VizGroup transform from a BasisN3 Motor](viz/scenes/motor_group_transform.md)

- **transforms** — [Demonstrate VizGroup + direct transforms](viz/scenes/scene_graph.md)

- **Translator** — [Gunn/Dorst PGA 3D geometry with plane‑based representation](ga/geometry/pga3_entities.md), [Rotor, Translator, Motor, Dilator visualization](viz/entities/operators.md)

- **translator** — [lift a 2D conic into a 3D cone through an apex](ga/quadric/cone_from_conic.md), [draw arbitrary quadrics via entities + GA translation](ga/quadric/general_quadric.md)

- **twist** — [BladeMask named bases (auto display basis, composed names, with_basis)](ga/blade_mask/named_basis.md)

- **TwistBivector** — [get_tensor() (raw MVTensor) + get_array() (named bases)](ga/expression/tensor_named_basis.md)

- **two points** — [Demo: Drag TWO 3D points interactively with ActPoint](viz/interaction/act_point_two.md), [Demo: Drag TWO 2D points interactively with ActPoint](viz/interaction/act_point_two_2d.md)

- **two-body** — [Gravitational two-body simulation using only](viz/animation/two_body_gravity.md)

- **underlay** — [fixed screen-space axes + grid overlay in 2D](viz/camera/axes_overlay_2d.md)

- **undo** — [Editable table: column types, keyboard nav, undo/redo](viz/ui/controls/table_editing.md)

- **uniform** — [Custom image shader that rotates RGB vectors](viz/image/custom_shader_rgb_rotate.md), [Display a numpy image and draw pixel-coordinate overlays](viz/image/image_canvas.md)

- **unify** — [Re-key variables so independent expressions merge](ga/expression/rename_unify_variables.md)

- **up vector** — [3D projective camera via View3dConfig](viz/camera/3d_plane.md)

- **update** — [Labels with custom styling, dynamic update, and removal](viz/labels/basic.md)

- **update in place** — [Animation](viz/jupyter/animation.md)

- **variable** — [Expressions, variables, and DataArray bindings](expression_dataarray.md)

- **Variable** — [Multi-variable linear equations with Variables](ga/expression/equation_demo.md), [Named GA product functions over variables](ga/expression/named_products.md), [Project an N3 expression onto the Euclidean basis](ga/expression/project_onto_euclidean_n3.md), [Re-key variables so independent expressions merge](ga/expression/rename_unify_variables.md), [Apply a fixed rotor to points with a Variable-backed expression](ga/expression/variable_rotor.md), [Rotate a list of points with a variable rotor and variable points](ga/expression/variable_rotor_entity.md)

- **variables** — [Multi-variable linear equations with Variables](ga/expression/equation_demo.md)

- **View2DConfig** — [2D orthographic view via View2DConfig](viz/camera/2d_view.md), [2D camera, axes, and grid basics](viz/camera/axes_grid_2d.md)

- **View3dConfig** — [3D projective camera via View3dConfig](viz/camera/3d_plane.md)

- **visualization** — [Least-squares line fitting in P3 with visualization](ga/expression/line_fitting_p3.md)

- **visualization-only** — [the visualization-only Cylinder and Arc entities](viz/entities/viz_entities.md)

- **visualizer** — [Interactive Visualizer](viz/jupyter/interactive.md)

- **Visualizer** — [Demonstrates every banner/dialog kind](viz/ui/banners/banner_types.md)

- **VisualizerApp** — [Two Spheres Intersection — Interactive Controls Demo (IPNS)](viz/interaction/two_spheres_interact.md), [Slider that triggers a blocking computation on release](viz/ui/banners/heavy_work.md), [Showcase every interactive control in one app](viz/ui/controls/all_controls.md), [A file chooser with a backend-driven file browser](viz/ui/controls/file_chooser.md), [An editable tabular-data control driven by the backend](viz/ui/controls/table_data.md)

- **VizGroup** — [A chaotic double pendulum from nested VizGroups](viz/animation/double_pendulum.md), [Compose a detached scene subtree, then insert it](viz/scenes/compose_detached.md), [Drive a VizGroup transform from a BasisN3 Motor](viz/scenes/motor_group_transform.md), [Demonstrate nested VizGroup hierarchies](viz/scenes/nested_groups.md), [Demonstrate VizGroup + direct transforms](viz/scenes/scene_graph.md)

- **VizSceneHandle** — [Banners scoped to a named scene via VizSceneHandle](viz/ui/banners/scene_banner.md)

- **VizSceneObject** — [Compose a detached scene subtree, then insert it](viz/scenes/compose_detached.md)

- **vp** — [Named GA product functions over variables](ga/expression/named_products.md)

- **weighted sum** — [Sum an AffineExpression over a batched variable](ga/expression/affine_counting_reduction.md)

- **wireframe** — [A custom theme with a full button/checkbox override](viz/ui/themes/custom_theme_override.md)

- **with_basis** — [BladeMask named bases (auto display basis, composed names, with_basis)](ga/blade_mask/named_basis.md)

## Topics

- [Geometric Algebra](ga/index.md)
- [Visualization](viz/index.md)
