import c4d
from c4d import gui
import c4d.modules.character

# Welcome to the world of Python

#
# POINT LEVEL WEIGHT COPY
# by Leah Anderson
#
# Tested on R20
#
# This script copies weights from one poly object to another on a new weight tag
# Please set it up as follows:
#
# You must select two objects in your scene..
#
# First / top object (just somewhere "above" in the scene object list) should be the object
# you are trying to copy weights from and that also contains the weight tag. You only
# have to select the polygon object itself, selecting the weight tag will make no diff
#
# Second / bottom object is going to be the object you are copying weights to. This object
# can contain a weight tag, or it cannot. The script will create a new weight tag on this object and
# apply everything there.
#
# SAVE FIRST and then click Execute. This is a brute force style algo so it is not fast!
# It is incredibly slow, but it works. C4D will appear frozen until the script completes.
#
# If someone wants to help me figure out how to do a progress bar that would be extremely awesome.
#
# Adjust "accuracy" threshold below if needed...


# Main function
def main():

    #POINT MATCH ACCURACY
    ac = 0.01

    doc = c4d.documents.GetActiveDocument()
    selected = doc.GetActiveObjects(0)

    fromObj = selected[0]
    toObj = selected[1]

    fromPointArr = []
    toPointArr = []

    cnt = fromObj.GetPointCount()
    for i in range(cnt):
        fromPointArr.append(fromObj.GetPoint(i))

    cnt = toObj.GetPointCount()
    for i in range(cnt):
        toPointArr.append(toObj.GetPoint(i))

    fromTag = fromObj.GetTag(c4d.Tweights)
    cnt = fromTag.GetJointCount()

    doc.StartUndo() #Start UndoBlock

    toTag = toObj.GetTag(c4d.Tweights)
    if not toTag:
        toTag = toObj.MakeTag(c4d.Tweights)
        doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,toTag)
        for i in range(cnt):
            toTag.AddJoint(fromTag.GetJoint(i))


    cnt2 = toTag.GetJointCount()
    print(str(cnt) + "source joints total")
    print(str(cnt2) + "dest joints total")
    pcnt = fromObj.GetPointCount()

    #i = joint index
    for i in range(cnt):
        joint = fromTag.GetJoint(i, doc)
        print ("SOURCE JOINT: " + joint.GetName() + " " + str(i))
        for k in range(cnt2):
            joint2 = toTag.GetJoint(k, doc)
            print("dest name ", joint2.GetName())
            if joint.GetName() == joint2.GetName():
                print("DEST JOINT: " + joint2.GetName() + " " + str(k))
                for j in range(len(fromPointArr)):
                    fromPointWeight = fromTag.GetWeight(i, j)
                    if fromPointWeight>0:
                        fromPoint = fromPointArr[j]
                        #print k
                        #print j
                        #print fromPointWeight
                        toTag.SetWeight(k, j, fromPointWeight)
                break;
    
    newSkin = c4d.BaseObject(c4d.Oskin)
    newSkin.InsertUnder(toObj)
    doc.AddUndo(c4d.UNDOTYPE_NEWOBJ,newSkin)

    doc.EndUndo()
    c4d.EventAdd()
    c4d.gui.StatusClear()

# Execute main()
if __name__=='__main__':
    main()