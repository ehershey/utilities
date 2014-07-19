getuserbydistro () 
{ 
    distro="$1";
    egrep --no-filename ^$distro:\|user: ~/git/mci/config*/distros.yml* ~/distros.yml* | grep -A 1 ^$distro: | tail -1 | cut -f2 -d: | tr -d " "
}

