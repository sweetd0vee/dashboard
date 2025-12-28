#!/usr/bin/env bash

script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
#echo $script_dir

cd $script_dir/../httpd
echo "Build httpd docker image"
pwd
./docker-build.sh

cd $script_dir/../postgres
echo "Build postgres docker image"
pwd
./docker-build.sh

cd $script_dir/../keycloak
echo "Build keycloak docker image"
pwd
./docker-build.sh


cd $script_dir/../ui
echo "Build ui docker image"
pwd
./docker-build.sh


cd $script_dir/../app
echo " Build app docker image"
pwd
./docker-build.sh


#read -rsn1 -p"Press any key to continue";echo
