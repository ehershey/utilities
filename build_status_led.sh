#!/bin/bash
#
# Pull build status from http://evergreen.mongodb.com/, display on BlinkyTape
#
#

set nounset

colors=""
$(dirname $0)/build_status.py | (while read build
do
	status=$(echo "$build" | cut -f2 -d,)
	build_variant_name=$(echo "$build" | cut -f1 -d,)
	echo "bv: $build_variant_name"
	echo status: $status
	color=""
	if [[ $status == "failed" ]]
	then
		color=red
	elif [[ $status == "success" ]]
	then
		color=green
	elif [[ $status == "incomplete" ]]
	then
		color="white"
	else
		echo "Skipping status: $status"
	fi
	echo color: $color
	colors="$colors $color"
	echo
done
echo calling $(dirname $0)/display_color_led.py $colors
$(dirname $0)/display_color_led.py $colors
)
