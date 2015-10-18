getuserbydistro ()
{
    distro="$1"
    name="$2"
    if echo $distro $name | grep windows > /dev/null 2>&1
    then
      echo Administrator
      return
    fi
    if echo $distro $name | grep ubuntu > /dev/null 2>&1
    then
      echo ubuntu
      return
    fi
    if echo $distro $name | grep amazon > /dev/null 2>&1
    then
      echo ec2-user
      return
    fi
    if echo $distro $name | grep amzn > /dev/null 2>&1
    then
      echo ec2-user
      return
    fi
    if echo $distro $name | grep suse > /dev/null 2>&1
    then
      echo ec2-user
      return
    fi


    user=$(
      grep -l ^$distro: ~/git/mci/config_prod/distros.yml* ~/git/mci/config_prod/distros/* ~/distros.yml* | xargs egrep --no-filename ^$distro:\|user: | grep -A 1 ^$distro: | grep -v ^$distro: | grep -v -- --  | tail -1 | cut -f2 -d: | tr -d " "
   )
    if [ ! "$user" ]
    then
      user=$(
        grep -l ^$distro: ~/git/mci/config_prod/distros.yml* ~/git/mci/config_prod/distros/* ~/distros.yml* | xargs egrep --no-filename ^$distro:\|user: | grep -B 1 ^$distro: | grep -v ^$distro: | grep -v -- -- | head -1 | cut -f2 -d: | tr -d " "
      )
    fi
    echo "$user"
}

