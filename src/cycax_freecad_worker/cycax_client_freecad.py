"""
This file is called directly from FreeCAD.

Run from command line. ./FreeCAD.AppImage cycax_part_freecad.py
"""

import logging
import os
import tempfile
import time
from math import sqrt
from pathlib import Path

import FreeCAD as App
import FreeCADGui
import importDXF
import importSVG

# import QtGui
import Part
import requests
from FreeCAD import Rotation, Vector  # NoQa
from PySide import QtGui

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.info("Opened in FreeCAD")

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"
REAR = "BACK"


class EngineFreecad:
    """This class will be used in FreeCAD to decode a JSON passed to it.
    The JSON will contain specific information of the object.

    Args:
        part_path: the path where the outputs need to be stored.
    """

    def cube(self, feature: dict):
        """This method will draw a cube when given a dict that contains the necessary dimensions

        Args:
            feature: This is the dict that contains the necessary details of the cube to be cut out.
        """
        if feature["center"] is True:
            x = feature["x"] - feature["x_size"] / 2
            y = feature["y"] - feature["y_size"] / 2
            z = feature["z"] - feature["z_size"] / 2
        else:
            x = feature["x"]
            y = feature["y"]
            z = feature["z"]
        pos_vec = (x, y, z)

        pos_vec = self._move_cube(feature, pos_vec, center=feature["center"])
        pos = Vector(pos_vec[0], pos_vec[1], pos_vec[2])
        length = feature["x_size"]
        width = feature["y_size"]
        depth = feature["z_size"]
        return Part.makeBox(length, width, depth, pos)

    def sphere(self, feature: dict):
        """This method will draw a sphere when given a dict that contains the necessary dimensions

        Args:
            feature: This is the dict that contains the necessary details of the sphere to be cut out.
        """
        x = feature["x"]
        y = feature["y"]
        z = feature["z"]
        pos_vec = (x, y, z)
        radius = feature["diameter"] / 2

        pos = Vector(pos_vec[0], pos_vec[1], pos_vec[2])
        return Part.makeSphere(radius, pos)

    def _calc_hex(self, depth: float, diameter: float):
        """This method will be used to find out where the points of the hexigon are located and then drawing a hexigon.

        Args:
            depth: this is the depth of the hexigon.
            diameter: this is the diameter of the hexigon.
        """

        radius = diameter / 2
        half_radius = radius / 2
        radius_sqrt = radius * sqrt(3) / 2
        vector_list = []
        z = depth

        vector_list.append(Vector(radius, 0, z))
        vector_list.append(Vector(half_radius, radius_sqrt, z))
        vector_list.append(Vector(-half_radius, radius_sqrt, z))
        vector_list.append(Vector(-radius, 0, z))
        vector_list.append(Vector(-half_radius, -radius_sqrt, z))
        vector_list.append(Vector(half_radius, -radius_sqrt, z))

        vector_list.append(vector_list[0])
        wire = Part.makePolygon(vector_list)
        shape = Part.Shape(wire)
        face = Part.Face(shape)
        return face

    def cut_nut(self, feature: dict):
        """This method will take the 2D hexigon and convert it to a 3D shape and place it where it needs to go.
        Args:
            feature: this is a dict containing the necessary details of the hexigon like its size and location.
        """

        hexigon = self._calc_hex(depth=0, diameter=feature["diameter"])
        nut = hexigon.extrude(App.Vector(0, 0, feature["depth"]))

        side = feature["side"]
        x = feature["x"]
        y = feature["y"]
        z = feature["z"]

        if feature["vertical"] is True:
            rotation1 = App.Rotation(Vector(0, 0, 1), 0)
        else:
            rotation1 = App.Rotation(Vector(0, 0, 1), 30)

        if side == FRONT:
            rotation2 = App.Rotation(Vector(1, 0, 0), 270)
        elif side == BACK:
            rotation2 = App.Rotation(Vector(1, 0, 0), 90)
        elif side == TOP:
            rotation2 = App.Rotation(Vector(0, 1, 0), 180)
        elif side == BOTTOM:
            rotation2 = App.Rotation(Vector(0, 1, 0), 0)
        elif side == LEFT:
            rotation2 = App.Rotation(Vector(0, 1, 0), 90)
        elif side == RIGHT:
            rotation2 = App.Rotation(Vector(0, 1, 0), 270)

        nut.Placement = App.Placement(Vector(x, y, z), rotation2 * rotation1)

        return nut

    def _move_cube(self, features: dict, pos_vec, *, center=False):
        """
        Accounts for when a cube is not going to penetrate the surface but rather sit above is.

        Args:
            features: This is the dictionary that contains the details of where the cube must be placed.
            pos_vec(list): where part is positioned.

        Returns:
        """

        angles = [0, 0, 0]
        if center is False:
            if features["side"] is not None:
                angles = features["side"]
                angles = {
                    TOP: [pos_vec[0], pos_vec[1], pos_vec[2] - features["z_size"]],
                    BACK: [pos_vec[0], pos_vec[1] - features["y_size"], pos_vec[2]],
                    BOTTOM: [pos_vec[0], pos_vec[1], pos_vec[2]],
                    FRONT: [pos_vec[0], pos_vec[1], pos_vec[2]],
                    LEFT: [pos_vec[0], pos_vec[1], pos_vec[2]],
                    RIGHT: [pos_vec[0] - features["x_size"], pos_vec[1], pos_vec[2]],
                }[angles]
        else:
            angles = [pos_vec[0], pos_vec[1], pos_vec[2]]

        return angles

    def hole(
        self,
        feature: dict | None = None,
        depth: float | None = None,
        radius: float | None = None,
        move: dict | None = None,
        side: str | None = None,
    ):
        """This method will be used for cutting a cylindrical hole into a surface.

        Args:
            feature: This is the dictionary that contains the details of where the hole must be placed and its details.
        """
        pos_vec = Vector(0, 0, 0)
        if feature is not None:
            cyl = Part.makeCylinder(feature["diameter"] / 2, feature["depth"], pos_vec)
            side = feature["side"]
            x = feature["x"]
            y = feature["y"]
            z = feature["z"]
        else:
            cyl = Part.makeCylinder(radius, depth, pos_vec)
            x = move["x"]
            y = move["y"]
            z = move["z"]
        if side == FRONT:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(1, 0, 0), 270))
        elif side == BACK:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(1, 0, 0), 90))
        elif side == TOP:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 180))
        elif side == BOTTOM:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 0))
        elif side == LEFT:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 90))
        elif side == RIGHT:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 270))
        return cyl

    def render_to_png(self, path: Path, view: str | None = None):
        """Used to create a png of the desired side.

        Args:
            view: The side of the object the png will be produced from.

        """
        active_doc = FreeCADGui.activeDocument()
        view = self.change_view(active_doc=active_doc, side=view, default="ALL")
        FreeCADGui.SendMsgToActiveView("ViewFit")

        target_image_file = path / f"view-{view}.png"
        active_doc.activeView().fitAll()
        active_doc.activeView().saveImage(str(target_image_file), 2000, 1800, "White")
        return target_image_file

    def change_view(
        self,
        active_doc: FreeCADGui.activeDocument,
        side: str,
        default: str | None = None,
    ):
        """This will change the gui view to show the specified side.
        Args:
            active_doc: Freecad active doc.
            side: The side the view is from.
            default: The default side for that view.
        """

        if side is None:
            side = default

        match side.upper().strip():
            case "TOP":
                active_doc.activeView().viewTop()
            case "BACK":
                active_doc.activeView().viewRear()
            case "REAR":
                active_doc.activeView().viewRear()
            case "BOTTOM":
                active_doc.activeView().viewBottom()
            case "FRONT":
                active_doc.activeView().viewFront()
            case "LEFT":
                active_doc.activeView().viewLeft()
            case "RIGHT":
                active_doc.activeView().viewRight()
            case "ALL":
                active_doc.activeView().viewAxometric()
            case _:
                msg = f"side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT BACK OR ALL."
                raise ValueError(msg)
        return side

    def render_to_dxf(self, path: Path, active_doc: App.Document, view: str | None = None) -> Path:
        """This method will be used for creating a dxf of the object currently in view.
        Args:
            active_doc: The FreeCAD document.
            view: The side from which to produce the output file.
        """
        view_doc = FreeCADGui.activeDocument()
        view = self.change_view(active_doc=view_doc, side=view, default="TOP")
        FreeCADGui.SendMsgToActiveView("ViewFit")
        __objs__ = []
        __objs__.append(active_doc.getObject("Shape"))

        target_image_file = path / f"view-{view}.dxf"
        importDXF.export(__objs__, str(target_image_file))
        return target_image_file

    def render_to_svg(self, path: Path, active_doc: App.Document, view: str | None = None) -> Path:
        """This method will be used for creating a svg of the object currently in view.
        Args:
            active_doc: The FreeCAD document.
            view: The side from which to produce the output file.
        """
        view_doc = FreeCADGui.activeDocument()
        view = self.change_view(active_doc=view_doc, side=view, default="TOP")
        FreeCADGui.SendMsgToActiveView("ViewFit")
        __objs__ = []
        __objs__.append(active_doc.getObject("Shape"))

        target_image_file = path / f"view-{view}.svg"
        importSVG.export(__objs__, str(target_image_file))
        return target_image_file

    def render_to_stl(self, path: Path, active_doc: App.Document):
        """This method will be used for creating a STL of an object currently in view.
        Args:
            active_doc: The FreeCAD document.
        """
        target_image_file = path / "model.stl"
        for obj in active_doc.Objects:
            if obj.ViewObject.Visibility:
                obj.Shape.exportStl(str(target_image_file))
                # NOTE: Moved the return into the Loop, need to see if this works.
                return target_image_file

    def _beveled_edge_cube(self, length: float, depth: float, side: str, move: dict):
        """
        Helper method for decode_beveled_edge.

        Args:
            length: Length of the beveled edge that will be cut.
            depth: Depth of the part.
            side: Side which the cutting will come from.
            center: set to True when the cube is centered at its center.
            rotate: set to True when the cube needs to be offset by 45 deg
        """

        x = move["x"]
        y = move["y"]
        z = move["z"]
        if side in [TOP, BOTTOM]:
            cube = Part.makeBox(length, length, depth, Vector(x, y, z))
        elif side in [FRONT, BACK]:
            cube = Part.makeBox(length, depth, length, Vector(x, y, z))
        elif side in [LEFT, RIGHT]:
            cube = Part.makeBox(depth, length, length, Vector(x, y, z))

        return cube

    def _rhombus(self, depth: float, length: float, move: dict, side: str):
        """This method will cut a rhombus with 90 degree andgles.

        Args:
            depth: this is the depth of the rhombus.
            length: this is the length of the rhombus.
            move: x, y, z of rhombut.
            side: side for rhombus to be cut into.
        """
        hypot = sqrt(length * 2 * length * 2 + length * 2 * length * 2) / 2
        vector_list = []

        vector_list.append(Vector(hypot, 0, 0))
        vector_list.append(Vector(0, hypot, 0))
        vector_list.append(Vector(-hypot, 0, 0))
        vector_list.append(Vector(0, -hypot, 0))

        vector_list.append(vector_list[0])
        wire = Part.makePolygon(vector_list)
        shape = Part.Shape(wire)
        face = Part.Face(shape)

        rhombus = face.extrude(App.Vector(0, 0, depth))

        x = move["x"]
        y = move["y"]
        z = move["z"]

        if side in [FRONT, BACK]:
            rhombus.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(1, 0, 0), 270))
        elif side in [TOP, BOTTOM]:
            rhombus.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 0, 1), 0))
        elif side in [LEFT, RIGHT]:
            rhombus.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 90))

        return rhombus

    def decode_beveled_edge(self, features: dict, solid):
        """
        This method will decode a beveled edge and either make a bevel or taper

        Args:
            features: This is the dictionary that contains the details of the beveled edge.
        """

        hypot = sqrt(features["size"] * 2 * features["size"] * 2 + features["size"] * 2 * features["size"] * 2) / 3
        move_cutter_cyl = {"x": 0, "y": 0, "z": 0}
        move_cutter_rhombus = {"x": 0, "y": 0, "z": 0}
        move_cube = {"x": 0, "y": 0, "z": 0}
        if features["bound1"] == 0:
            move_cutter_cyl[features["axis1"]] = features["size"]
            move_cutter_rhombus[features["axis1"]] = hypot
            move_cube[features["axis1"]] = 0
        else:
            move_cutter_cyl[features["axis1"]] = features["bound1"] - features["size"]
            move_cutter_rhombus[features["axis1"]] = features["bound1"] - hypot
            move_cube[features["axis1"]] = features["bound1"] - features["size"]
        if features["bound2"] == 0:
            move_cutter_cyl[features["axis2"]] = features["size"]
            move_cutter_rhombus[features["axis2"]] = hypot
            move_cube[features["axis2"]] = 0
        else:
            move_cutter_cyl[features["axis2"]] = features["bound2"] - features["size"]
            move_cutter_rhombus[features["axis2"]] = features["bound2"] - hypot
            move_cube[features["axis2"]] = features["bound2"] - features["size"]

        if features["edge_type"] == "round":
            cutter = self.hole(
                radius=features["size"],
                depth=features["depth"],
                side=features["side"],
                move=move_cutter_cyl,
            )

        elif features["edge_type"] == "chamfer":
            cutter = self._rhombus(
                depth=features["depth"],
                length=features["size"],
                move=move_cutter_rhombus,
                side=features["side"],
            )

        cube = self._beveled_edge_cube(
            length=features["size"],
            depth=features["depth"],
            side=features["side"],
            move=move_cube,
        )

        cutter = cube.cut(cutter)
        res = solid.cut(cutter)
        Part.cast_to_shape(res)

        return res

    def construct_from_features(self, doc, features: list[dict], part_path: Path) -> Path:
        cut_features = []
        for feature in features:
            if feature["type"] == "add":
                solid = self.cube(feature)
            elif feature["type"] == "cut":
                if feature["name"] == "hole":
                    cut_features.append(self.hole(feature))
                elif feature["name"] == "beveled_edge":
                    solid = self.decode_beveled_edge(feature, solid)
                elif feature["name"] == "cube":
                    cut_features.append(self.cube(feature))
                elif feature["name"] == "sphere":
                    solid = solid.cut(self.sphere(feature))
                    # This was necessary to avoid creating a shape that was too complicate for FreeCAD to follow.
                elif feature["name"] == "nut":
                    cut_features.append(self.cut_nut(feature))

        logging.info("Features applied")
        if len(cut_features) > 1:
            s1 = cut_features.pop()
            fused = s1.multiFuse(cut_features)
            result = solid.cut(fused)
        elif len(cut_features) == 1:
            s1 = cut_features.pop()
            result = solid.cut(s1)
        else:
            result = solid

        Part.show(result)
        doc.recompute()
        logging.info("Part created")
        FreeCADGui.activeDocument().activeView().viewTop()
        FreeCADGui.SendMsgToActiveView("ViewFit")

        filepath = part_path / "freecad.FCStd"
        doc.saveCopy(str(filepath))
        logging.info("Part Saved: %s", filepath)
        return filepath

    def build(self, part_path: Path, definition: dict) -> list[Path]:
        """
        Build the part in FreeCAD.

        Args:
            part_path:
            job:
        """

        if "name" not in definition:
            definition["name"] = definition["id"]
        name = definition["name"]
        logging.info("Definition loaded for: %s", name)

        if App.ActiveDocument:
            App.closeDocument(name)
        doc = App.newDocument(name)
        file_list = []
        file_list.append(self.construct_from_features(doc, definition["features"], part_path))
        outformats = "PNG,STL,DXF"
        for out_choice in outformats.upper().split(","):
            ftype = out_choice
            fview = None
            out_format = ftype.strip()
            match out_format:
                case "PNG":
                    file_list.append(self.render_to_png(part_path, view=fview))
                case "DXF":
                    file_list.append(self.render_to_dxf(part_path, view=fview, active_doc=doc))
                case "SVG":
                    file_list.append(self.render_to_svg(part_path, view=fview, active_doc=doc))
                case "STL":
                    file_list.append(self.render_to_stl(part_path, active_doc=doc))
                case _:
                    msg = f"file_type: {out_format} is not one of PNG, DXF or STL."
                    raise ValueError(msg)
        App.closeDocument(name)
        # QtGui.QApplication.quit()
        return file_list


def get_jobs(server_address) -> dict:
    """Find the next job to work on.

    The jobs_path variable should point to a directory containing symlinks
    to cycax parts. Each part directory is evaluated to see if there is an
    JSON definition for the part.

    Args:
        jobs_path: The directory with symlinks to parts to process.

    """
    while True:
        reply = requests.get(server_address + "/jobs/", timeout=20)
        job_list = reply.json().get("data", [])
        # TODO: Consider randomising the list so two instances of FreeCAD take different files.
        if not job_list:
            time.sleep(2)
            continue
        for job in job_list:
            if job.get("attributes", {}).get("state", {}).get("job") == "CREATED":
                # TODO: Do a take & check here.
                yield job
    return None


def get_job_spec(server_address: str, job: dict) -> dict:
    """Fetch the Job Spec of a Job."""
    reply = requests.get(server_address + f"/jobs/{job['id']}/spec", timeout=20)
    job_spec = reply.json().get("data", [])
    return job_spec


def upload_file(url: str, filepath: Path):
    logging.info("Upload file %s to %s", filepath, url)
    files = {"upload_file": filepath.read_bytes()}
    file_details = {"filename": filepath.name}
    response = requests.post(url, files=files, data=file_details, timeout=20)
    logging.info(response)


def upload_files(server_address: str, job: dict, file_list: list[Path]):
    url = server_address + f"/jobs/{job['id']}/artifacts"
    for filepath in file_list:
        retry = 3
        while retry > 0:
            try:
                upload_file(url, filepath)
            except Exception:
                retry -= 1
                time.sleep(3)
            else:
                break  # out of the while loop
        if retry == 0:
            break  # out of the for loop, dont go into else.
    else:
        # Success
        url = server_address + f"/jobs/{job['id']}/state"
        response = requests.get(url, timeout=20)
        logging.info(response)


def main(cycax_server_address: str):

    engine = EngineFreecad()
    task_counter = 5
    for job in get_jobs(cycax_server_address):
        with tempfile.TemporaryDirectory() as tmpdirname:
            task_counter -= 1
            part_path = Path(tmpdirname)
            job_spec = get_job_spec(cycax_server_address, job)
            _start = time.time()
            file_list = engine.build(part_path, job_spec)
            logging.warning("Part creation took %s seconds", time.time() - _start)
            upload_files(cycax_server_address, job, file_list)
            if task_counter < 0:
                logging.warning("Done enough work, I quit. Should run this with a service manager that can restart me.")
                break


if os.environ.get("PYTEST_VERSION") is None:
    # Not in the unit test.
    # START
    cycax_server_address = os.getenv("CYCAX_SERVER").strip("/")
    if cycax_server_address is None:
        logging.error("CYCAX_SERVER environment variable is not defined or set.")
        QtGui.QApplication.quit()

    try:
        main(cycax_server_address)
    except Exception:
        logging.exception("Unexpected")
    logging.info("End of application. Normal termination.")
    QtGui.QApplication.quit()
