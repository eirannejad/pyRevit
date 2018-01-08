"""List all currently loaded assemblies"""

from pyrevit import framework


__context__ = 'zerodoc'


userScriptsAssemblies = []
for loadedAssembly in framework.AppDomain.CurrentDomain.GetAssemblies():
    loc = ''
    if 'pyrevit' in unicode(loadedAssembly.FullName).lower():
        userScriptsAssemblies.append(loadedAssembly)
        continue
    try:
        loc = loadedAssembly.Location
    except Exception:
        pass
    print('\n{0}{1}{2}'.format(loadedAssembly.GetName().Name.ljust(50),
                               str(loadedAssembly.GetName().Version).ljust(20),
                               loc))
    try:
        print('External Applications:')
        print([x.FullName
               for x in loadedAssembly.GetTypes()
               if x.GetInterface("IExternalApplication") is not None])
    except Exception:
        pass
    try:
        print('External Commands:')
        print([x.FullName
               for x in loadedAssembly.GetTypes()
               if x.GetInterface("IExternalCommand") is not None])
    except Exception:
        pass

print('\n\nPYREVIT ASSEMBLIES:')
for loadedAssembly in userScriptsAssemblies:
    loc = ''
    try:
        loc = loadedAssembly.Location
    except Exception:
        pass
    print('{0}{1}{2}'.format(loadedAssembly.GetName().Name.ljust(50),
                             str(loadedAssembly.GetName().Version).ljust(20),
                             loc))
    try:
        print('External Commands:')
        print([x.FullName
               for x in loadedAssembly.GetTypes()
               if x.GetInterface("IExternalCommand") is not None])
        print('\n')
    except Exception:
        pass
