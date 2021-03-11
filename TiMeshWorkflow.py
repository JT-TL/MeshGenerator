import os
import sys
import threaded_trimatic as t
import time

PARA = {
    "TI_MESH_THICKNESS": 0.3, 
    "SOLID_MARGIN_WIDTH": 0.6, 
    "MAXIMUM_TRIANGLE_EDGE_LENGTH": 5, 
    "POROSITY": 70, 
    "HOLES_NUMBERS": 7, 
    "HOLES_RADIUS": 0.1, 
    "LATTICE_THICKNESS": 0.3, 
}

def ti_mesh_step1_prepare(ui):
    # Create new project and import the STL file
    t.new_project()
    file_path = os.getcwd() + "\\Janus001.stl"
    arch_original = t.import_part_stl(file_path)
    print(os.getcwd())
    print(file_path)
    arch_original.visible = False

    # Preprocessing the bone arch
    temp = t.duplicate(arch_original)
    t.reduce(entities=temp, geometrical_error=0.05)
    t.smooth(entities=temp, smooth_factor=0.3, perform_post_processing=True)
    arch_prepared = t.wrap(
        entities=temp, 
        gap_closing_distance=0, 
        smallest_detail=0.5, 
        resulting_offset=0.05
        )
    t.delete(temp)
    # t.reduce(entities=arch_wrapped, geometrical_error=0.05)
    arch_prepared.name = arch_original.name + "_prepared"
    t.view_default(view=t.DefaultViews.Right)

# -------------------------------- Create the curve -------------------------------------

def ti_mesh_step2_sketch(ui):
    # Check the curve
    print("Step2: Create the midplane.")
    arch_prepared = t.find_part("Janus001_prepared")
    surface_curve = arch_prepared.find_curve("Curve")
    if not surface_curve.closed:
        print("Please make sure the curve is closed")
    if not surface_curve.fully_attached:
        print("Please make sure the curve is fully attached")
    t.view_default(view=t.DefaultViews.Front)

    # Indicate the points to create the sketch
    print("Please indicate one point.")
    point_1_coords = t.indicate_coordinate()
    point_1 = t.create_point(coords=point_1_coords)

    print("Please indicate another point.")
    point_2_coords = t.indicate_coordinate()
    point_2 = t.create_point(coords=point_2_coords)

    # Create midplane
    sagittal_plane = t.create_plane_midplane(point1=point_1, point2=point_2)
    sagittal_sketch = t.create_sketch(sagittal_plane)
    sagittal_plane.visible=False
    sagittal_sketch.visible=False

    # Mirror the wrapped arch around the sagittal sketch
    temp = t.duplicate(arch_prepared)
    origin = sagittal_plane.origin
    normal = sagittal_plane.normal
    arch_mirrored = t.mirror(temp, origin=origin, normal=normal)
    arch_mirrored.name = "Janus001_mirrored"

    # Create coronal sketch
    x_axis = sagittal_plane.x_axis
    coronal_sketch = t.rotate(
        entities=sagittal_sketch, 
        angle_deg=90, 
        axis_origin=origin, 
        axis_direction=x_axis, 
        number_of_copies=1
        )
    t.translate(entities=coronal_sketch, translation_vector=(25, 10, 10))
    coronal_sketch.name = "sketch_coronal"
    t.delete([point_1, point_2, sagittal_plane, sagittal_sketch])
    t.set_selection(arch_mirrored)
    ui.proceed_to_next_step()

# -------------------------------- Skipped -------------------------------------

def ti_mesh_step3_interactive_translate(ui):
    print("Step3 executed: ti_mesh_step3_interactive_translate")
    t.view_default(view=t.DefaultViews.Top)

    

# -------------------------------- Adjust the arch -------------------------------------

def ti_mesh_step4_draw_spline(ui):
    print("Step4 executed: ti_mesh_step4_draw_spline")
    # Find entities
    arch_prepared = t.find_part("Janus001_prepared")
    arch_mirrored = t.find_part("Janus001_mirrored")
    sketch_coronal = t.find_sketch("sketch_coronal")
    surface_curve = arch_prepared.find_curve("Curve")

    # Importing sketch outline
    t.import_intersection(construction=True, entities=arch_mirrored, sketch=sketch_coronal)
    t.import_intersection(construction=True, entities=arch_prepared, sketch=sketch_coronal)
    t.import_intersection(construction=True, entities=surface_curve, sketch=sketch_coronal)

    arch_prepared.visible = False
    arch_mirrored.visible = False
    t.view_default(view=t.DefaultViews.Back)
    t.zoom(sketch_coronal)

# -------------------------------- Draw spline -------------------------------------

def ti_mesh_step5_construct_surface(ui):
    print("Step5 executed: ti_mesh_step5_construct_surface")
    # Find entities
    arch_prepared = t.find_part("Janus001_prepared")
    sketch_coronal = t.find_sketch("sketch_coronal")
    surface_curve = arch_prepared.find_curve("Curve")

    # Surface construction
    arch_prepared.visible = False
    sketch_coronal.visible = False
    surface = t.surface_construction(entities=surface_curve, guiding_lines=sketch_coronal)
    prosthesis = t.move_to_part(surface)
    prosthesis.name = "Titanium Scaffold"

    # Surface trim
    t.adaptive_remesh_expert(
        entities=prosthesis, 
        maximum_geometrical_error=0.05, 
        minimum_triangle_edge_length=0.05, 
        maximum_triangle_edge_length=0.5, 
        preserve_surface_contours=True
        )
    arch_prepared.visible = True
    arch_prepared.transparency = 0.8
    sketch_coronal.visible = False
    t.view_default(view=t.DefaultViews.Top)

# -------------------------------- Mark triangles -------------------------------------

def ti_mesh_step6_surface_refinement(ui):
    print("Step6: ti_mesh_step6_surface_refinement executed.")
    # Find entities
    arch_prepared = t.find_part("Janus001_prepared")
    prosthesis = t.find_part("Titanium Scaffold")
    arch_prepared.visible = False
    marked_triangles = prosthesis.get_marked_triangles()
    t.delete(marked_triangles)

    # Smooth surface contour
    surface_border = prosthesis.get_surfaces()[0].get_border()
    t.smooth_curve(entities=surface_border, smooth_factor=0.5, treat_as_free_curve=False)

    # Isolate surface contour and split surface
    surface_contour = prosthesis.get_surfaces()[0].get_border().get_contours()[0]
    iso_curve = t.create_iso_curves(
        entities=surface_contour, 
        interval_distance=PARA["SOLID_MARGIN_WIDTH"], 
        number_of_copies=1, 
        direction=t.DirectionMethod.inside
        )
    t.smooth_curve(entities=iso_curve, smooth_factor=0.5)
    iso_curve = t.attach_curve(entities=iso_curve, target_entities=prosthesis)
    print("Start split!")
    try:
        surface_set = t.split_surfaces_by_curves(curves=iso_curve)
    except Exception as e:
        print("this is the bug")
        print(e)
    print("Split Done!")

    if surface_set[0].area > surface_set[1].area:
        surface_inner = surface_set[0]
        surface_outer = surface_set[1]
    else:
        surface_inner = surface_set[1]
        surface_outer = surface_set[0]
    surface_inner.name = "inner_surface"
    surface_outer.name = "outer_surface"

    arch_original = t.find_part("Janus001")
    arch_original.visible = True
    t.view_default(view=t.DefaultViews.Isometric)


# -------------------------------- Surface refinement -------------------------------------

def ti_mesh_step7_create_graph(ui):
    # Find entities
    arch_original = t.find_part("Janus001")
    arch_original.visible = False
    prosthesis = t.find_part("Titanium Scaffold")
    prosthesis.visible = False
    inner_surface_buttom = prosthesis.find_surface("inner_surface")
    outer_surface_buttom = prosthesis.find_surface("outer_surface")

    surface_borders = outer_surface_buttom.get_border()
    t.smooth_curve(entities=surface_borders, smooth_factor=0.5, treat_as_free_curve=False)

    solid_margin = t.copy_to_part(outer_surface_buttom)
    solid_margin.name = "solid_margin"
    t.adaptive_remesh_expert(
        entities=solid_margin, 
        maximum_geometrical_error=0.05, 
        minimum_triangle_edge_length=0.5, 
        maximum_triangle_edge_length=5, 
        preserve_surface_contours=True
        )
    t.smooth(entities=solid_margin, smooth_factor=0.6, perform_post_processing=True)
    solid_margin = t.uniform_offset_preserve_sharp_features(solid_margin.get_surfaces()[0], PARA["TI_MESH_THICKNESS"], solid=True)

    inner_surface_mid = t.copy_to_part(inner_surface_buttom)
    inner_surface_mid.name = "inner_surface_mid"
    surface_top = t.copy_to_part(prosthesis.get_surfaces())
    surface_top.name = "surface_top"

    t.uniform_offset(inner_surface_mid, PARA["TI_MESH_THICKNESS"]/2)
    t.smooth_curve(entities=inner_surface_mid.get_surfaces()[0].get_border(), smooth_factor=0.5)
    t.uniform_offset(surface_top, PARA["TI_MESH_THICKNESS"])
    t.smooth_curve(entities=surface_top.get_surfaces()[0].get_border(), smooth_factor=0.5)
    surface_top.visible = False

    t.quality_preserving_reduce_triangles(
        entities=inner_surface_mid, 
        shape_measure=t.ShapeMeasures.equi_angle_skewness_n, 
        shape_quality_threshold=0.3, 
        maximum_geometrical_error=0.5, 
        maximum_triangle_edge_length=PARA["MAXIMUM_TRIANGLE_EDGE_LENGTH"], 
        number_of_iterations=5, 
        preserve_surface_contours=False
        )
    t.smooth(entities=inner_surface_mid, smooth_factor=0.5, perform_post_processing=False)
    graph = t.mesh_based_lattice(entities=inner_surface_mid)
    graph.name = "graph"
    

# -------------------------------- Mark graph beam -------------------------------------

def ti_mesh_step8_create_holes(self):
    # find entities
    prosthesis = t.find_part("Titanium Scaffold")
    inner_surface_mid = t.find_part("inner_surface_mid")
    surface_top = t.find_part("surface_top")
    solid_margin = t.find_part("solid_margin")
    graph = inner_surface_mid.find_graph("graph")

    t.set_graph_properties(entities=graph, thickness=PARA["LATTICE_THICKNESS"], accuracy=0.05)
    lattice = t.convert_lattice_to_mesh(entities=graph)
    lattice.name = "lattice"
    t.delete(lattice.get_surfaces()[0])
    t.quality_preserving_reduce_triangles(
        entities=lattice, 
        shape_measure=t.ShapeMeasures.equi_angle_skewness_n, 
        shape_quality_threshold=0.36, 
        maximum_geometrical_error=0.05, 
        maximum_triangle_edge_length=0.3, 
        number_of_iterations=5, 
        preserve_surface_contours=False
        )
    unioned = t.boolean_union([solid_margin, lattice])
    arch_prepared = t.wrap(
        entities=unioned, 
        gap_closing_distance=0, 
        smallest_detail=0.05, 
        resulting_offset=0.01
        )



ti_mesh_steps = {
    "s1":("Create surface contour", ti_mesh_step1_prepare, "Create a curve around the atrophied area of the alvealor bone. Make sure the curve is counter-clockwise. Use a smooth curve that is closed, attracted and attached."), 
    "s2":("Create midplane", ti_mesh_step2_sketch, "Select two points on the either side of the mandible such that the midplane corresponds to the mirror plane of the arch. (Mental foramen is recommanded.)"), 
    "s3":("Reposition arch", ti_mesh_step3_interactive_translate, "Use Interactive Translate/Rotate tool to manually repotition the mirrored arch to fill the defect of the arch."), 
    "s4":("Create guideline", ti_mesh_step4_draw_spline, "Use Sketch to create spline as a guideline.The goal is to match the mirrored arch and use the imported points as beginning and ending points."), 
    "s5":("Mark triangles", ti_mesh_step5_construct_surface, "Mark triangles that need to be trimed. Use wave mark tool and hold Shift to mark through."), 
    "s6":("Done", ti_mesh_step6_surface_refinement, "Hit Exit to quit."), 
    "s7":("Surface refinement", ti_mesh_step7_create_graph, "Use mark beam tool to mark short dense beams, and then delete them mannuly."), 
    "s8":("Create holes", ti_mesh_step8_create_holes, "Select %d points on the inner surface to create holes for the screw. " % PARA["HOLES_NUMBERS"])
}

ti_mesh_step_guid_images = ["ti_mesh_1.png", "ti_mesh_2.png", "ti_mesh_3.png", "ti_mesh_4.png", "ti_mesh_5.png", "ti_mesh_6.png", "ti_mesh_7.png", "ti_mesh_8.png"]


    





    



