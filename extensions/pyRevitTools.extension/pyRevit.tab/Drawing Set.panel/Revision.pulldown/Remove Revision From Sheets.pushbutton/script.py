"""Remove selected revisions from selected sheets."""

from pyrevit import revit, DB
from pyrevit import forms


__doc__ = 'Select a revision from the list of revisions\n'\
          'and this script will remove that revision ' \
          'from all sheets if it has not been "clouded" on the sheet.'


def print_sheet(sht):
    snum = sht.Parameter[DB.BuiltInParameter.SHEET_NUMBER].AsString().rjust(10)
    sname = sht.Parameter[DB.BuiltInParameter.SHEET_NAME].AsString().ljust(50)
    print('NUMBER: {0}   NAME:{1}'.format(snum, sname))


revisions = forms.select_revisions(button_name='Select Revision',
                                   multiselect=True)

if revisions:
    sheets = forms.select_sheets(button_name='Set Revision')
    if sheets:
        with revit.Transaction('Remove Revision from Sheets'):
            updated_sheets = revit.update.update_sheet_revisions(revisions,
                                                                 sheets,
                                                                 state=False)
        if updated_sheets:
            print('SELECTED REVISION REMOVED FROM THESE SHEETS:')
            print('-' * 100)
            cloudedsheets = []
            for s in sheets:
                if s in updated_sheets:
                    print_sheet(s)
                else:
                    cloudedsheets.append(s)
        else:
            cloudedsheets = sheets

        if len(cloudedsheets) > 0:
            print('\n\nSELECTED REVISION IS CLOUDED ON THESE SHEETS '
                  'AND CAN NOT BE REMOVED.')
            print('-' * 100)

            for s in cloudedsheets:
                print_sheet(s)
