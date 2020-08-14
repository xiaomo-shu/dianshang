from PyInstaller.utils.hooks import collect_submodules
hiddenimports = collect_submodules('django_redis.compressors')
