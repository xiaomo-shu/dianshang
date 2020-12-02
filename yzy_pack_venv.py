import os
import sys
import time
import traceback
import PyInstaller.__main__

from configparser import ConfigParser
from argparse import ArgumentParser
from datetime import datetime
from subprocess import Popen, PIPE


CUR_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
PARSER = ArgumentParser(description='Yzy kvmproject builder.')

PARSER.add_argument("version",
                    help="Current package version")
PARSER.add_argument("sversion",
                    help="Support upgrade from version")
PARSER.add_argument("service",
                    help="The service need to pack")
PARSER.add_argument("dest",
                    help="Package build output path")
PARSER.add_argument("-s", "--src",
                    help="Source code root path, default '/data/workspace/'",
                    default="/data/workspace/")
PARSER.add_argument("-conf", "--conf",
                    help="The build conf path, default is under current path, name is 'build.ini'",
                    default=os.path.join(CUR_DIR, "build.ini"))


TMP_WORK_DIR = r'/tmp/tmp_dir'
YI_DESK = 'Yi_Desk_VDI'
KVM_NAME = 'yzy_kvmprojects'
EXCLUED_PACKAGES = ['yzy_pack.py']

def exec_cmd(cmd, uid=0, cwd=None):
    print("execute cmd ", cmd)
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False,
                 preexec_fn=lambda: os.setuid(uid), cwd=cwd)
    out, err = proc.communicate()
    return proc.returncode, out, err


def run():
    time_str = time.time()
    arg = PARSER.parse_args()
    config = ConfigParser()
    config.read(arg.conf)
    source_dir = os.path.join(arg.src, KVM_NAME)
    dest_path = arg.dest
    package_list = os.listdir(source_dir)
    for package in package_list:
        if package == arg.service:
            try:
                print("start pack ", package)
                _d = {
                    'entry_filename': None,
                    'paths': None,
                    'binary': None,
                    'hooks_dir': None,
                    'hidden_import': None,
                    'add_data': None
                }
                for key in _d.keys():
                    if config.has_option(package.upper(), key):
                        _d[key] = config.get(package.upper(), key)

                if _d['binary'] is None:
                    _d['binary'] = []

                package_dir = os.path.join(source_dir, package)
                cmd = [
                    os.path.join(source_dir, package, _d['entry_filename']),
                    '--onefile',
                    '--clean',
                    '--distpath=%s' % dest_path,
                    '--workpath=%s' % os.path.join(TMP_WORK_DIR, package, 'bulid'),
                    '--specpath=%s' % os.path.join(TMP_WORK_DIR, package),
                    '--name=%s' % package,
                    '--paths=%s' % package_dir,
                ]
                if _d['paths']:
                    for path in _d['paths'].split(','):
                        cmd.append('--paths=%s' % (os.path.join(package_dir, path)))
                if _d['hooks_dir']:
                    for hook in _d['hooks_dir'].split(','):
                        cmd.append('--additional-hooks-dir=%s' % (os.path.join(package_dir, hook)))

                if _d['binary']:
                    if not os.path.isabs(_d['binary']):
                        for binary in _d['binary'].split(','):
                            src = os.path.join(package_dir, binary.split(':')[0])
                            dst = binary.split(':')[1]
                            cmd.append('--add-binary=%s' % ('%s:%s' % (src, dst)))
                        # _d['binary'] = os.path.join(package_dir, _d['binary'])
                    else:
                        cmd.append('--add-binary=%s' % _d['binary'])
                # add_data的dst指定了打包后的脚本
                if _d['add_data']:
                    for data in _d['add_data'].split(','):
                        src = os.path.join(package_dir, data)
                        dst = "/usr/local/yzy-kvm/%s/" % data
                        cmd.append('--add-data=%s' % ('%s:%s' % (src, dst)))

                if _d['hidden_import']:
                    _d['hidden_import'] = _d['hidden_import'].split(',')
                    cmd.extend(['--hidden-import=%s' % hi for hi in _d['hidden_import']])

                print(' '.join(cmd))

                print('------------------------%s 开始打包------------------------' % package)
                PyInstaller.__main__.run(cmd)
                print('------------------------%s 打包完成------------------------' % package)
            except Exception as e:
                print('------------EEROR------------%s 打包失败： %s' % (package, e))
                traceback.print_exc()
    time_end = time.time()
    spend = (time_end - time_str)
    print("spend time %s" % spend)
    # shutil.rmtree(dest_path, True)


if __name__ == '__main__':
    run()
