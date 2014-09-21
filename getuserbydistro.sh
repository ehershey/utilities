getuserbydistro () 
{ 
    distro="$1";
    if echo $distro | grep windows > /dev/null 2>&1
    then
      echo Administrator
      return
    fi
    user=$(egrep --no-filename ^$distro:\|user: ~/git/mci/config_prod/distros.yml* ~/git/mci/config_prod/distros/* ~/distros.yml* | grep -A 1 ^$distro: | tail -1 | cut -f2 -d: | tr -d " ")
    if [ ! "$user" ]
    then
      user=$(egrep --no-filename ^$distro:\|user: ~/git/mci/config_prod/distros.yml* ~/git/mci/config_prod/distros/* ~/distros.yml* | grep -B 1 ^$distro: | tail -1 | cut -f2 -d: | tr -d " ")
    fi
    echo "$user"
}

