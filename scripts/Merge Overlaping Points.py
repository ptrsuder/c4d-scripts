import c4d
import math

def main():
    
    # Set your desired tolerance in centimeters
    merge_tolerance_cm = 0.01  # distance in cm 
    
    # Get active object
    obj = doc.GetActiveObject()
    if obj is None:
        raise RuntimeError("No object selected")   
    
    # Undo setup
    doc.StartUndo()
    doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
    
    # Execute merge
    merge_points_with_tolerance(obj, merge_tolerance_cm)
    
    # Finalize undo
    doc.EndUndo()
    c4d.EventAdd()


def merge_points_with_tolerance(obj, tolerance_cm=0.1):
    """
    Merge overlapping points within a specified tolerance distance in centimeters.
    
    Args:
        obj (c4d.PolygonObject): The object to process
        tolerance_cm (float): Maximum distance between points to merge (in cm)
    """
    if not obj.IsInstanceOf(c4d.Opolygon):
        raise TypeError("Selected object is not a PolygonObject")
    
    # Convert tolerance to squared distance for efficient comparison
    tolerance_squared = tolerance_cm * tolerance_cm
    
    points = obj.GetAllPoints()
    polygons = obj.GetAllPolygons()
    point_count = obj.GetPointCount()
    
    if point_count == 0:
        return False
    
    # Prepare data structures
    unique_points = []
    point_map = [0] * point_count
    new_points = []
    
    def find_similar_point_index(point):
        """Find index of first point within tolerance, or None if no match"""
        for i, unique_pt in enumerate(unique_points):
            if (point - unique_pt).GetLengthSquared() <= tolerance_squared:
                return i
        return None
    
    # Process all points
    for i, point in enumerate(points):
        similar_idx = find_similar_point_index(point)
        
        if similar_idx is not None:
            # Point is similar to an existing unique point
            point_map[i] = similar_idx
        else:
            # New unique point found
            point_map[i] = len(unique_points)
            unique_points.append(point)
    
    # Early exit if no merging needed
    if len(unique_points) == point_count:
        print("No points within tolerance found")
        return False
    
    # Update polygons with new point indices
    new_polygons = []
    for poly in polygons:
        new_poly = c4d.CPolygon(
            point_map[poly.a],
            point_map[poly.b],
            point_map[poly.c],
            point_map[poly.d]
        )
        new_polygons.append(new_poly)
    
    # Resize and update the object
    obj.ResizeObject(len(unique_points), len(new_polygons))
    obj.SetAllPoints(unique_points)
    for i, poly in enumerate(new_polygons):
        obj.SetPolygon(i, poly)
    
    # Finalize changes
    obj.Message(c4d.MSG_UPDATE)
    c4d.EventAdd()
    
    print(f"Merged {point_count - len(unique_points)} points (tolerance: {tolerance_cm} cm)")
    return True

if __name__ == '__main__':
    main()