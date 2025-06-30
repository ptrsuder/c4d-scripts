###This plugin iterates through all materials attached to an object and splits it to sepperate objects. It also cleans up UV tiling, so the
###object can be exported to other allications
###by Matthaeus Niedoba: matniedoba.de

import c4d
from c4d import documents, utils, Vector

def walk(op):
    if not op: return
    elif op.GetDown():
        return op.GetDown()
    while op.GetUp() and not op.GetNext():
        op = op.GetUp()
    return op.GetNext()

#Transform texture projection to UVW
def createUVW(obj):
    tex = obj.GetTag(c4d.Ttexture)
    if not tex : return

    if tex[c4d.TEXTURETAG_PROJECTION]!=6:
        for i in obj.GetTags():
            if i.CheckType(c4d.Tuvw):
                i.Remove()
        doc.SetActiveTag(tex)
        c4d.CallCommand(12235)   # Generate UVW Coordinates
        doc.SetActiveTag(None)

def nb_dec(n) :
    n = abs(n)
    dec = n - int(n)
    nb = str(dec)
    nb = len(nb) - 2
    return nb

#Modify coordinates -> Credits to César Vonc: https://code.vonc.fr/?a=20
def modif_coor(p, tex, lcX, lcY) :
    p -= Vector(tex[c4d.TEXTURETAG_OFFSETX], tex[c4d.TEXTURETAG_OFFSETY], 0)

    if lcX is True :
        p.x /= tex[c4d.TEXTURETAG_LENGTHX]
    else :
        p.x *= tex[c4d.TEXTURETAG_TILESX]

    if lcY is True :
        p.y /= tex[c4d.TEXTURETAG_LENGTHY]
    else :
        p.y *= tex[c4d.TEXTURETAG_TILESY]

    return p

#Cleanup offset and scale values
def cleanUVW(obj) :
    tex = obj.GetTag(c4d.Ttexture)
    if not tex : return
    uvw = obj.GetTag(c4d.Tuvw)
    if not uvw : return

    polys = uvw.GetDataCount()
    lcX  = True # Longueur ou Carreaux X
    lcY  = True # Longueur ou Carreaux Y
    if nb_dec(tex[c4d.TEXTURETAG_TILESX]) < nb_dec(tex[c4d.TEXTURETAG_LENGTHX]*100) :
        lcX = False
    if nb_dec(tex[c4d.TEXTURETAG_TILESY]) < nb_dec(tex[c4d.TEXTURETAG_LENGTHY]*100) :
        lcY = False

    for i in range(polys):
        uvwdict = uvw.GetSlow(i)
        a = modif_coor(uvwdict["a"], tex, lcX, lcY)
        b = modif_coor(uvwdict["b"], tex, lcX, lcY)
        c = modif_coor(uvwdict["c"], tex, lcX, lcY)
        d = modif_coor(uvwdict["d"], tex, lcX, lcY)
        uvw.SetSlow(i, a, b, c, d)

    tex[c4d.TEXTURETAG_OFFSETX] = 0
    tex[c4d.TEXTURETAG_OFFSETY] = 0
    tex[c4d.TEXTURETAG_LENGTHX] = 1
    tex[c4d.TEXTURETAG_LENGTHY] = 1
    tex[c4d.TEXTURETAG_TILESX] = 1
    tex[c4d.TEXTURETAG_TILESY] = 1

#check if material has alpha applied
def checkAlpha (tag):
    mat = tag[c4d.TEXTURETAG_MATERIAL]
    if mat[c4d.MATERIAL_USE_ALPHA]==1:return True
    else: return False

#check if Selection Tag is empty
def checkEmpty(tag):
    sel = None
    for i in tag.GetObject().GetTags():
        if i.CheckType(c4d.Tpolygonselection) and tag[c4d.TEXTURETAG_RESTRICTION] == i.GetName():
            sel = i
    #Check if Selection has no polygons
    if sel.GetBaseSelect().GetCount()==0: return True
    else: return False

#Clean Tags
def cleanTags(obj,tag):
    for i in obj.GetTags():
        if i.CheckType(c4d.Ttexture) and i[c4d.TEXTURETAG_MATERIAL]!=tag[c4d.TEXTURETAG_MATERIAL]: i.Remove()
        if i.CheckType(c4d.Tpolygonselection): i.Remove()
        if i.CheckType(c4d.Ttexture): i[c4d.TEXTURETAG_RESTRICTION]=""
    #Rremove double or multiple Texture Tags
    tempTag = None
    for i in obj.GetTags():
        if i.CheckType(c4d.Ttexture) and tempTag == None:
            tempTag = obj.GetFirstTag()
        elif i.CheckType(c4d.Ttexture) :
            i.Remove()

#Copy Object and Clean Tags
def copyObject (obj,tag):
    newObj = obj.GetClone()
    newObj.SetName(tag[c4d.TEXTURETAG_MATERIAL].GetName())

    cleanTags(newObj,tag)
    return newObj

#Split polygonselection to a new object and Clean Tags
def copySelection(obj,tag):

    #deselect current polygonselection
    polyselection = obj.GetPolygonS()
    polyselection.DeselectAll()

    #select polygons from selectiontag
    for i in obj.GetTags():
        if tag[c4d.TEXTURETAG_RESTRICTION]== i.GetName()and i.CheckType(c4d.Tpolygonselection):
                tagselection  =  i.GetBaseSelect()
                tagselection.CopyTo(polyselection)

    sec = utils.SendModelingCommand(command=c4d.MCOMMAND_SPLIT,
                                    list=[obj],
                                    mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
                                    doc=documents.GetActiveDocument())
    newObj = sec[0]
    newObj.SetName(tag[c4d.TEXTURETAG_MATERIAL].GetName())
    cleanTags(newObj,tag)
    return newObj

#Delete selected polygons, split polygonselection to a new object and Clean Tags
def splitObject(obj,tag,delete):
    #deselect current polygonselection
    polyselection = obj.GetPolygonS()
    polyselection.DeselectAll()

    #select polygons from selectiontag
    for i in obj.GetTags():
        if tag[c4d.TEXTURETAG_RESTRICTION] == i.GetName() and i.CheckType(c4d.Tpolygonselection):
            tagselection  =  i.GetBaseSelect()
            tagselection.CopyTo(polyselection)

    sec = utils.SendModelingCommand(command=c4d.MCOMMAND_SPLIT,
                                    list=[obj],
                                    mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
                                    doc=documents.GetActiveDocument())
    #delete the polygons from selectiontag
    if delete:
        utils.SendModelingCommand(command=c4d.MCOMMAND_DELETE,
                                    list=[obj],
                                    mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
                                    doc=documents.GetActiveDocument())

    newObj = sec[0]
    newObj.SetName(tag[c4d.TEXTURETAG_MATERIAL].GetName())

    cleanTags(newObj,tag)

    #Optimize Rest obj
    utils.SendModelingCommand(command=c4d.MCOMMAND_OPTIMIZE,
                                    list=[obj],
                                    mode=c4d.MODELINGCOMMANDMODE_ALL,
                                    doc=documents.GetActiveDocument())
    return newObj

#transform polygon object with tags to null with children
def proceedObject(obj,progress,numAllTextures):
    if obj.CheckType(c4d.Opolygon)==False:
        return
    
    hasSkin = False
    for i in obj.GetChildren():
        if i.CheckType(c4d.Oskin):
            hasSkin = True
            break

    tags = obj.GetTags()
    newObjs=[]
    for i in reversed(tags):
        if i.CheckType(c4d.Ttexture):
            progress+=1
            c4d.gui.StatusSetText("Exporting "+str(progress)+"of "+str(numAllTextures))
            c4d.gui.StatusSetBar(100.0*progress/numAllTextures)
            if i[c4d.TEXTURETAG_RESTRICTION]!="":
                sel = i[c4d.TEXTURETAG_RESTRICTION]
            else: sel = None
            if sel == None:
                newObjs.append( copyObject (obj,i))
                print("append1")
            elif sel != None and checkEmpty(i)==False:
                newObjs.append(copySelection (obj,i))
                print("append2")
            #elif sel != None and checkAlpha(i)==False and checkEmpty(i)==False:
                #newObjs.append(splitObject(obj,i,True))
                #print("splitObject")

    #Create new nullobject
    nullObj = c4d.BaseObject(c4d.Onull)
    nullObj.SetName(obj.GetName())
    #Insert objects under null
    for i in newObjs:
        i.InsertUnder(nullObj)
        i.SetAbsPos(c4d.Vector(0,0,0))
        i.SetAbsRot(c4d.Vector(0,0,0))
        i.SetAbsScale(c4d.Vector(1,1,1))
        if hasSkin:
            newSkin = c4d.BaseObject(c4d.Oskin)
            newSkin.InsertUnder(i)
    return nullObj

def main():

    doc = c4d.documents.GetActiveDocument()

    objs = documents.GetActiveDocument().GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)
    nb = len(objs)
    if nb == 0 : return False

    #For calculating the Progress Bar
    numAllTextures = 0
    progress = 0
    newObjs = [] #List for new null objects
    objListMM = [] #Object list with multiple texture tags
    objListMS = [] #Object list with multiple selection tags
    #Collect all objects
    for i in objs:
        if i.CheckType(c4d.Opolygon):
            numTextures = 0
            for j in i.GetTags():
                if j.CheckType(c4d.Ttexture):
                    numTextures+=1
                    numAllTextures+=1
                if numTextures>1 and i not in objListMM:
                    objListMM.append(i)

    doc.StartUndo() #Start UndoBlock

    for i in objListMM: #Insert and delete objects
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, i)
        tempObj = proceedObject(i,progress,numAllTextures)
        tempObj.InsertAfter(i)
        tempObj.SetMg(i.GetMg())
        doc.AddUndo(c4d.UNDOTYPE_NEW, tempObj)
        doc.AddUndo(c4d.UNDOTYPE_DELETE,i)
        i.Remove()
        newObjs.append(tempObj)

        #Optimize UVWS
        for j in tempObj.GetChildren():
            createUVW(j)
            cleanUVW(j)

    doc.EndUndo()
    #Perform selection
    doc.SetActiveObject(None,c4d.SELECTION_NEW)
    for i in newObjs:
        doc.SetSelection(i,c4d.SELECTION_ADD)

    c4d.EventAdd()
    c4d.gui.StatusClear()

    return True

if __name__ == '__main__':
    main()