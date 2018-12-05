"""List all view that are referring the selected viewports."""


from pyrevit import revit, DB
from pyrevit import script


output = script.get_output()


selection = revit.get_selection()
views = DB.FilteredElementCollector(revit.doc)\
          .OfCategory(DB.BuiltInCategory.OST_Views)\
          .WhereElementIsNotElementType()\
          .ToElements()


all_views = []
all_ref_els = []


for el in DB.FilteredElementCollector(revit.doc)\
            .WhereElementIsNotElementType()\
            .ToElements():
    if el.Category \
            and isinstance(el, DB.Element) \
            and str(el.Category.Name).startswith('View'):
        all_ref_els.append(el.Id)


class ReferencingView:
    def __init__(self, view_id):
        self.element = doc.GetElement(view_id)
        if not self._valid_view():
            raise Exception()

        title = self.element.LookupParameter('Title on Sheet').AsString()
        self.name = title if title else self.element.ViewName
        self.refs = []
        self._update_refs(all_ref_els)
        # self._update_refs(self.element.GetReferenceCallouts())
        # self._update_refs(self.element.GetReferenceSections())
        # self._update_refs(self.element.GetReferenceElevations())

        self.sheet_num = \
            self.element.LookupParameter('Sheet Number').AsString()
        self.sheet_name = \
            self.element.LookupParameter('Sheet Name').AsString()
        self.ref_det = \
            self.element.LookupParameter('Detail Number').AsString()

    def __repr__(self):
        return '<{} on sheet: {} - {} Refs>'\
               .format(self.name, self.sheet_num, len(self.refs))

    def _valid_view(self):
        return isinstance(self.element,
                          (DB.ViewDrafting, DB.ViewPlan, DB.ViewSection))

    def _update_refs(self, el_list):
        for elid in el_list:
            el = doc.GetElement(elid)
            if el.OwnerViewId == self.element.Id:
                self.refs.append(el.Name)

    def is_referring_to(self, view_name):
        return view_name in self.refs

    def is_sheeted(self):
        return self.sheet_num != ''


print('Collecting all view references in all view...')

for view in views:
    try:
        rv = ReferencingView(view.Id)
        all_views.append(rv)
    except Exception:
        pass


print('{} views processed...'.format(len(all_views)))

for selid in selection:
    vp = revit.doc.GetElement(selid)
    if isinstance(vp, DB.Viewport):
        v = revit.doc.GetElement(vp.ViewId)
        title = v.LookupParameter('Title on Sheet').AsString()
        print('\n\nVIEW NAME: {}\n    Referenced by:'
              .format(title if title else v.ViewName))

        for r_view in all_views:
            if r_view.is_sheeted() \
                    and r_view.is_referring_to(v.ViewName):
                print('\t\t{} : {}/{} : {}'
                      .format(output.linkify(r_view.element.Id),
                              r_view.ref_det,
                              r_view.sheet_num,
                              r_view.name))
