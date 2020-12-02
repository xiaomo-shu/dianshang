#!/bin/bash
version=$1
sversion=$2
upgrade=$3
src="/data/workspace"
yi_desk="Yi_Desk_VDI"
kvm_name="yzy_kvmprojects"
cur_date=`date +%Y%m%d`
version_info=$yi_desk"_"$version"_"$cur_date
source_dir=$src"/"$kvm_name
py_dir=$src"/pyinstall/"$version_info
dest=$py_dir"/build/"$kvm_name
pack_py='yzy_pack_venv.py'
venv_dir='/data/workspace/venv'

if [ $# -ne 3 ];then
  echo "`basename $0` version sversion self-upgrade"
  exit
fi
# 服务打包
deployment_dir=$src"/control-node-deployment"
deployment_dest_dir=$source_dir"/yzy_deployment"
/bin/cp -r $deployment_dir $deployment_dest_dir
$venv_dir"/deployment_venv/bin/python" $pack_py $version $sversion yzy_deployment $dest --src $src
/bin/cp -r $deployment_dir"/static" $dest
/bin/cp -r $deployment_dir"/templates" $dest
rm -rf $deployment_dest_dir
$venv_dir"/server_venv/bin/python" $pack_py $version $sversion yzy_upgrade $dest --src $src
$venv_dir"/compute_venv/bin/python" $pack_py $version $sversion yzy_compute $dest --src $src
$venv_dir"/monitor_venv/bin/python" $pack_py $version $sversion yzy_monitor $dest --src $src
$venv_dir"/server_venv/bin/python" $pack_py $version $sversion yzy_server $dest --src $src
$venv_dir"/terminal_venv/bin/python" $pack_py $version $sversion yzy_terminal $dest --src $src
$venv_dir"/terminal_agent_venv/bin/python" $pack_py $version $sversion yzy_terminal_agent $dest --src $src
$venv_dir"/ukey_venv/bin/python" $pack_py $version $sversion yzy_ukey $dest --src $src
web_dir=$source_dir"/yzy_web"
web_dest_dir=$source_dir"/yzy_web_app"
mv $web_dir $web_dest_dir
$venv_dir"/web_venv/bin/python" $pack_py $version $sversion yzy_web_app $dest --src $src
mv $web_dest_dir $web_dir
# 将前端代码、配置文件和数据库初始化文件移入
/bin/cp -r $source_dir"/config" $dest
/bin/cp -r $source_dir"/html" $dest
/bin/cp -f $source_dir"/common/yzy_kvm_db_init.sql" $dest
echo $version_info >  $dest"/version"
# 压缩包打包
cd $py_dir"/build"
tar zcf $py_dir"/"$kvm_name".tar.gz" $kvm_name
# 升级包打包
if [ $version != $sversion ];then
  rm -f $dest"/yzy_kvm_db_init.sql"
  if [ "$upgrade" = "true" ];then
    touch $dest"/need_self_upgrade"
  fi
  touch $dest"/sversion"
  echo $sversion > $dest"/sversion"
  upgrade_dir=$src"/upgrade_scripts/"$version"/"$sversion
  if [ -d $upgrade_dir ];then
    /bin/cp -rf $upgrade_dir $dest"/upgrade_scripts"
  fi
  cd $py_dir"/build"
  tar zcf $py_dir"/"$kvm_name"-"$version"-"$sversion"-upgrade.tar.gz" $kvm_name
fi
