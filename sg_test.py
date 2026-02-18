import PySimpleGUI as sg
print('has Window', hasattr(sg,'Window'))
print('has theme', hasattr(sg,'theme') or hasattr(sg,'Theme'))
print('module type', type(sg))
print('version', getattr(sg,'__version__', 'unknown'))
print('dir sample:', [name for name in dir(sg) if name.lower().startswith('w')][:20])
