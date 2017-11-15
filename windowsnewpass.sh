#
# The new password will be randomly generated.
# It will be suitable for logging into the host via RDP.
# SSH access should use standard ssh keypairs.
#
# Usage:
# windowsnewspass.sh [ <new password> ]
#
# If you don't specify a password, a random new one will be generated.
#
# Must be run in Cygwin.
#
#

if [ "$1" ]
then
  password="$1"
  if ! net user Administrator "$password"
  then
    echo "Setting password failed. Aborting"
    exit 2
  fi
else

  echo "Generating random password..."
  # This command can sometimes fail
  #
  while ! net user Administrator /random > /tmp/rdp_password.out 2>&1
  do
          echo "Retrying to generate sufficient random password."
  done
  echo "Done."


  password="$(grep "Password for Administrator is:" /tmp/rdp_password.out | cut -f2 -d: | tr -d \ )"
fi
echo "Setting password on sshd service."

sc config sshd obj= '.\Administrator' password= "$password"
echo "Done."
echo "New password is: $password"
