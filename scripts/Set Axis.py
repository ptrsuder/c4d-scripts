"""
Sets the axis to selected object.
Also handles vertices and normal tags.
Corrected to handle non-uniform scaling.

Based on script by ferdinand
http://developers.maxon.net/forum/post/67961
"""

import c4d
import array
import math

def main() -> None:
    """Entry point that runs the code when there is an active object."""
    if not op:
        c4d.gui.MessageDialog("Please select an object.")
        return

    #Set to desired PSR:
    mgTarget = psr_to_matrix(
                                c4d.Vector(0,0,0),
                                c4d.Vector(1,1,1),
                                c4d.Vector(0,0,0))

    TransferAxisTo(op, mgTarget)
    c4d.EventAdd()


def psr_to_matrix(pos: c4d.Vector, scale: c4d.Vector, rot_degrees: c4d.Vector) -> c4d.Matrix:
    """Converts Position, Scale, and Rotation values into a c4d.Matrix.

    Args:
        pos: The position vector (offset).
        scale: The scale vector.
        rot_degrees: The rotation vector in HPB (Heading, Pitch, Bank) order, in degrees.

    Returns:
        A c4d.Matrix representing the combined transformation.
    """
    # 1. Convert rotation from degrees to radians for C4D utilities
    rot_radians = c4d.Vector(
        math.radians(rot_degrees.x),
        math.radians(rot_degrees.y),
        math.radians(rot_degrees.z)
    )

    # 2. Create a rotation-only matrix (v1, v2, v3 are normalized)
    # The rotation order in C4D is typically Heading, Pitch, Bank (Y, X, Z)
    # which corresponds to the default order of HPBToMatrix.
    m = c4d.utils.HPBToMatrix(rot_radians, c4d.ROTATIONORDER_HPB)

    # 3. Apply the scale to the matrix's axis vectors and set the offset
    m.off = pos
    m.v1 = m.v1 * scale.x
    m.v2 = m.v2 * scale.y
    m.v3 = m.v3 * scale.z

    return m

def transpose_matrix(m: c4d.Matrix) -> c4d.Matrix:
    """Manually transposes a c4d.Matrix's 3x3 orientation part."""
    return c4d.Matrix(
        off=c4d.Vector(0),
        v1=c4d.Vector(m.v1.x, m.v2.x, m.v3.x),
        v2=c4d.Vector(m.v1.y, m.v2.y, m.v3.y),
        v3=c4d.Vector(m.v1.z, m.v2.z, m.v3.z)
    )

def ReadNormalTag(tag: c4d.NormalTag) -> list[c4d.Vector]:
    """Reads a `c4d.NormalTag` to a list of c4d.Vector."""
    if not (isinstance(tag, c4d.BaseTag) and tag.CheckType(c4d.Tnormal)):
        msg = f"Expected normal tag, received: {tag}."
        raise TypeError(tag)

    buffer = tag.GetLowlevelDataAddressR()
    if buffer is None:
        msg = "Failed to retrieve memory buffer for VariableTag."
        raise RuntimeError(msg)

    data = array.array('h')
    data.frombytes(buffer)
    # Convert the int16 representation of the normals to c4d.Vector.
    return [c4d.Vector(data[i-3] / 32000.0,
                       data[i-2] / 32000.0,
                       data[i-1] / 32000.0)
            for i in range(3, len(data) + 3, 3)]


def WriteNormalTag(tag: c4d.NormalTag, normals: list[c4d.Vector],
                   normalize: bool = True) -> None:
    """Writes a list of c4d.Vector to a `c4d.NormalTag`."""
    if not (isinstance(tag, c4d.BaseTag) and tag.CheckType(c4d.Tnormal)):
        msg = f"Expected normal tag, received: {tag}."
        raise TypeError(tag)

    buffer = tag.GetLowlevelDataAddressW()
    if buffer is None:
        msg = "Failed to retrieve memory buffer for VariableTag."
        raise RuntimeError(msg)

    if normalize:
        normals = [n.GetNormalized() for n in normals]

    # For a Tnormal tag, GetDataCount() returns the number of polygons.
    # The tag stores 4 normals per polygon.
    polygon_count = tag.GetDataCount()
    expected_normal_count = polygon_count * 4

    if len(normals) != expected_normal_count:
        msg = (f"Invalid data size. The NormalTag has {polygon_count} polygons "
               f"and expects {expected_normal_count} normals. "
               f"The provided list contains {len(normals)} normals.")
        raise IndexError(msg)

    # Convert c4d.Vector normals to integer representation.
    raw_normals = [int(component * 32000.0)
                   for n in normals for component in (n.x, n.y, n.z)]

    # Write the data back.
    data = array.array('h')
    data.fromlist(raw_normals)
    data = data.tobytes()
    buffer[:len(data)] = data


def TransferAxisTo(node: c4d.BaseObject, mgTarget: c4d.Matrix) -> None:
    """Moves the axis of node to target, baking the transformation into the
    points and normals, correctly handling non-uniform scale.
    """
    mgNode = node.GetMg()

    doc.StartUndo()
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, node)

    node.SetMg(mgTarget)

    if not isinstance(node, c4d.PointObject):
        doc.EndUndo()
        return

    mgDelta = ~mgTarget * mgNode

    try:
        orientation_delta = c4d.Matrix(v1=mgDelta.v1, v2=mgDelta.v2, v3=mgDelta.v3)
        inverse_orientation_delta = ~orientation_delta
        mgNormalDelta = transpose_matrix(inverse_orientation_delta)
    except:
        c4d.gui.MessageDialog("Could not calculate normal transformation. The object might have a scale of zero on an axis. Normals may be incorrect.")
        mgNormalDelta = c4d.Matrix()

    node.SetAllPoints([p * mgDelta for p in node.GetAllPoints()])
    node.Message(c4d.MSG_UPDATE)

    normalTag = node.GetTag(c4d.Tnormal)
    if not isinstance(normalTag, c4d.NormalTag):
        doc.EndUndo()
        return

    try:
        current_normals = ReadNormalTag(normalTag)
        newNormals = [n * mgNormalDelta for n in current_normals]
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, normalTag)
        WriteNormalTag(normalTag, newNormals, normalize=True)
    except (TypeError, RuntimeError, IndexError) as e:
        print(f"An error occurred while writing to the normal tag: {e}")
        c4d.gui.MessageDialog(f"An error occurred while writing to the normal tag: {e}")

    doc.EndUndo()

if __name__ == '__main__':
    main()