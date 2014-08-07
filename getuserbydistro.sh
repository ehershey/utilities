getuserbydistro () 
{ 
    distro="$1";
    user=$(egrep --no-filename ^$distro:\|user: ~/git/mci/config*/distros.yml* ~/distros.yml* | grep -A 1 ^$distro: | tail -1 | cut -f2 -d: | tr -d " ")
    if [ ! "$user" ]
    then
      user=$(egrep --no-filename ^$distro:\|user: ~/git/mci/config*/distros.yml* ~/distros.yml* | grep -B 1 ^$distro: | tail -1 | cut -f2 -d: | tr -d " ")
    fi
    echo "$user"
}

