from pyrevit import revit, DB
from pyrevit import script
from pyrevit import forms


logger = script.get_logger()


views = DB.FilteredElementCollector(revit.doc)\
          .OfCategory(DB.BuiltInCategory.OST_Views)\
          .WhereElementIsNotElementType()\
          .ToElements()


def GetElementCenter(el, v):
    cen = el.Location.Point
    z = (el.UpperLimit.Elevation + el.LimitOffset) / 2
    cen = cen.Add(DB.XYZ(0, 0, z))
    return cen


def tag_all_rooms():
    rooms = DB.FilteredElementCollector(revit.doc)\
              .OfCategory(DB.BuiltInCategory.OST_Rooms)\
              .WhereElementIsNotElementType()\
              .ToElements()

    with revit.Transaction('Tag All Rooms in All Views'):
        for v in views:
            for el in rooms:
                room_center = GetElementCenter(el, v)
                if type(v) in [DB.ViewSection, DB.ViewPlan]:
                    logger.debug('Working on view: %s' % v.ViewName)
                    roomtag = \
                        revit.doc.Create.NewRoomTag(
                            DB.LinkElementId(el.Id),
                            DB.UV(room_center.X, room_center.Y),
                            v.Id
                            )
                    if isinstance(v, DB.ViewSection):
                        roomtag.Location.Move(DB.XYZ(0, 0, room_center.Z))


def tag_all_spaces():
    spaces = DB.FilteredElementCollector(revit.doc)\
              .OfCategory(DB.BuiltInCategory.OST_MEPSpaces)\
              .WhereElementIsNotElementType()\
              .ToElements()

    with revit.Transaction('Tag All Spaces in All Views'):
        for v in views:
            for el in spaces:
                room_center = GetElementCenter(el, v)
                if type(v) in [DB.ViewSection, DB.ViewPlan]:
                    logger.debug('Working on view: %s' % v.ViewName)
                    roomtag = \
                        revit.doc.Create.NewRoomTag(
                            DB.LinkElementId(el.Id),
                            DB.UV(room_center.X, room_center.Y),
                            v.Id
                            )
                    if isinstance(v, DB.ViewSection):
                        roomtag.Location.Move(DB.XYZ(0, 0, room_center.Z))


options_dict = {'Tag All Rooms in All Views': tag_all_rooms,
                'Tag All Spaces in All Views': tag_all_spaces}

selected_switch = \
    forms.CommandSwitchWindow.show(options_dict.keys())

option_func = options_dict.get(selected_switch, None)

if option_func:
    option_func()
