"""
Copyright (c) 2016 Gui Talarico

CopyPasteViewportPlacemenet
Copy and paste the placement of viewports across sheets
github.com/gtalarico | gtalarico@gmail.com

--------------------------------------------------------
pyRevit Notice:
pyRevit: repository at https://github.com/eirannejad/pyRevit

"""

__doc__ = 'Copy a Viewport Placement into memory'
__author__ = 'Gui Talarico | gtalarico@gmail.com'
__version__ = '0.1.0'

import os
import pickle
from tempfile import gettempdir
from collections import namedtuple

from Autodesk.Revit.DB import Viewport
from Autodesk.Revit.UI import TaskDialog

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

Point = namedtuple('Point', ['X', 'Y','Z'])

selected_ids = uidoc.Selection.GetElementIds()

if selected_ids.Count == 1:
    for element_id in selected_ids:
        element = doc.GetElement(element_id)
        if isinstance(element, Viewport):
            center = element.GetBoxCenter()
            pt = Point(center.X, center.Y, center.Z)
            temp = os.path.join(gettempdir(), 'ViewPlacement')
            with open(temp, 'wb') as fp:
                pickle.dump(pt, fp)
            print('Viewport Saved')
            break
else:
    TaskDialog.Show('pyRevitPlus', 'Select 1 Viewport. No more, no less!')

__window__.Close()
