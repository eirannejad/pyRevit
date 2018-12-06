"""Prints all available emojis with shorthand codes."""
from pyrevit.coreutils.loadertypes import ScriptOutputEmojis

from pyrevit import script

output = script.get_output()


__context__ = 'zerodoc'

output.freeze()
for e in ScriptOutputEmojis.emojiDict.Keys:
    print(':{0}: : {0}'.format(e))
output.unfreeze()