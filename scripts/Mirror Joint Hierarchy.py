import c4d

def get_selected_joints(doc):
    """Retrieve all selected joints in the current document."""
    selected_joints = []

    # Get all currently selected objects
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)

    for obj in selection:
        if obj.GetType() == c4d.Ojoint:
            selected_joints.append(obj)

    return selected_joints

def add_mirror_constraint(joint, target_joint):
    # Check if joint already has a constraint tag
    constraint_tag = None
    for tag in joint.GetTags():
        if tag.GetType() == c4d.Tcaconstraint:
            constraint_tag = tag

    # If not found, create new constraint tag
    if not constraint_tag:
        constraint_tag = joint.MakeTag(c4d.Tcaconstraint)
        doc.AddUndo(c4d.UNDOTYPE_NEW, constraint_tag)
        constraint_tag.SetParameter(c4d.ID_CA_CONSTRAINT_TAG_MIRROR, True, c4d.DESCFLAGS_SET_USERINTERACTION)

        constraint_tag[70009,1000] = True
        constraint_tag[70009,1001] = True

        constraint_tag[70009,1004] = c4d.ID_CA_CONSTRAINT_TAG_MIRROR_AXIS_YZ
        constraint_tag[70009,1005] = c4d.ID_CA_CONSTRAINT_TAG_MIRROR_AXIS_YZ

        constraint_tag[70001] = target_joint

        constraint_tag[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
        constraint_tag[c4d.ID_CA_CONSTRAINT_TAG_LOCAL_S] = True
        constraint_tag[10005] = False
        constraint_tag[10007] = False
        constraint_tag[10006] = True
        constraint_tag[10001] = target_joint

    return

def main():
    doc = c4d.documents.GetActiveDocument()

    # Define sides   

    left_prefixes = ["arm left", "leg left"]
    right_prefixes = ["arm right", "leg right"]

    obj_list = get_selected_joints(doc)

    doc.StartUndo()
    for obj in obj_list:
        #print(obj.GetName())
        for i in range(len(left_prefixes)):
            left_prefix = left_prefixes[i]
            right_prefix = right_prefixes[i]

            if obj.GetName().startswith(left_prefix):
                #print(right_prefix)
                # Generate corresponding name for right-side object
                corresponding_name = obj.GetName().replace(left_prefix, right_prefix)
                #print(corresponding_name)

                # Find corresponding object
                corresponding_obj = doc.SearchObject(corresponding_name)

                if not corresponding_obj:
                    continue

                add_mirror_constraint(corresponding_obj ,obj)
    
    doc.EndUndo()
    
c4d.EventAdd()

if __name__=='__main__':
  main()