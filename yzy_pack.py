import os
import sys
import time
import shutil
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
PARSER.add_argument("-self", "--self",
                    help="if need upgrade self",
                    default="true")
PARSER.add_argument("-s", "--src",
                    help="Source code root path, default '/data/workspace/'",
                    default="/data/workspace/")
PARSER.add_argument("-dest", "--dest",
                    help="Package build output path, default '/data/workspace/pyinstall/'",
                    default="/data/workspace/pyinstall/")
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
    version_info = '%s_%s_%s' % (YI_DESK, arg.version, datetime.now().strftime("%Y%m%d"))
    kvm_path = os.path.join(arg.dest, version_info, "build")
    dest_path = os.path.join(kvm_path, KVM_NAME)
    # 打包时要求外层名字与里面那个目录不一样，所以重命名一下，打包完再重命名回来
    source = os.path.join(source_dir, "yzy_web")
    dest = os.path.join(source_dir, "yzy_web_app")
    shutil.move(source, dest)
    # 这里是拷贝初始化的工程进行打包，打包完之后删除
    deploy_dir = os.path.join(arg.src, "control-node-deployment")
    dest_deploy = os.path.join(source_dir, "yzy_deployment")
    if os.path.exists(deploy_dir):
        shutil.copytree(deploy_dir, dest_deploy)
    package_list = os.listdir(source_dir)
    for package in package_list:
        if package.startswith('yzy') and package not in EXCLUED_PACKAGES:
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

    shutil.move(dest, source)
    if os.path.exists(dest_deploy):
        shutil.rmtree(dest_deploy)

    # config是所有服务相关的配置文件存放地点
    config_dir = os.path.join(dest_path, "config")
    # html是前端js代码
    html_dir = os.path.join(dest_path, "html")
    # static和templates是初始化工程相关的前端代码
    static_dir = os.path.join(dest_path, "static")
    templates_dir = os.path.join(dest_path, "templates")
    if os.path.exists(config_dir):
        shutil.rmtree(config_dir)
    if os.path.exists(html_dir):
        shutil.rmtree(html_dir)
    if os.path.exists(static_dir):
        shutil.rmtree(static_dir)
    if os.path.exists(templates_dir):
        shutil.rmtree(templates_dir)
    shutil.copytree(os.path.join(source_dir, "config"), config_dir)
    shutil.copytree(os.path.join(source_dir, "html"), html_dir)
    shutil.copytree(os.path.join(deploy_dir, "static"), static_dir)
    shutil.copytree(os.path.join(deploy_dir, "templates"), templates_dir)
    shutil.copy(os.path.join(source, '.secrets.toml'), config_dir)
    # sql文件是初始化时用作创建数据库表的脚本
    shutil.copy(os.path.join(source_dir, "common", "yzy_kvm_db_init.sql"), dest_path)
    file_path = os.path.join(arg.dest, version_info, KVM_NAME + '.tar.gz')
    version_file = os.path.join(dest_path, "version")
    with open(version_file, 'w') as fd:
        fd.write(version_info)
        fd.write("\n")
    build_tar_package(file_path, kvm_path)
    print("安装包打包完成")
    # 升级包打包
    if arg.version != arg.sversion:
        # shutil.rmtree(config_dir, True)
        shutil.rmtree(static_dir, True)
        shutil.rmtree(templates_dir, True)
        try:
            os.remove(os.path.join(dest_path, 'yzy_kvm_db_init.sql'))
        except:
            pass
        upgrade_path = os.path.join(arg.dest, version_info, KVM_NAME + '-%s-%s-upgrade.tar.gz' % (arg.version, arg.sversion))
        sversion_file = os.path.join(dest_path, "sversion")
        if arg.self == "true":
            upgrade_flag = os.path.join(dest_path, "need_self_upgrade")
            with open(upgrade_flag, 'w') as fd:
                fd.write("")
        with open(sversion_file, 'w') as fd:
            fd.write(arg.sversion)
            fd.write("\n")
        upgrade_dir = os.path.join(arg.src, 'upgrade_scripts')
        script_path = os.path.join(upgrade_dir, arg.version, arg.sversion)
        if os.path.exists(script_path):
            upgrade_script_path = os.path.join(dest_path, "upgrade_scripts")
            shutil.rmtree(upgrade_script_path, True)
            shutil.copytree(script_path, upgrade_script_path)
        build_upgrade_package(upgrade_path, kvm_path)
        print("升级包打包完成")
    shutil.rmtree(TMP_WORK_DIR, True)
    time_end = time.time()
    spend = (time_end - time_str)/60
    print("spend time %s" % spend)
    # shutil.rmtree(dest_path, True)


def build_tar_package(file_path, dir_path):
    cmd = ["tar", "zcf", file_path] + os.listdir(dir_path)
    code, out, err = exec_cmd(cmd, cwd=dir_path)
    if code:
        raise Exception("out %s, err %s" % (out, err))


def build_upgrade_package(file_path, dir_path):
    cmd = ["tar", "zcf", file_path] + os.listdir(dir_path)
    code, out, err = exec_cmd(cmd, cwd=dir_path)
    if code:
        raise Exception("out %s, err %s" % (out, err))


if __name__ == '__main__':
    run()
