from PyInstaller.utils.hooks import collect_submodules
hiddenimports = collect_submodules('yzy_web.wsgi.application')
