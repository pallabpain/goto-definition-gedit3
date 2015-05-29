#!/bin/sh
#
# Installs the plugin to the users plugin folder

PLUGINS_FOLDER=~/.local/share/gedit/plugins

install_file() {
	echo " - adding $1 to $PLUGINS_FOLDER"
	cp "$1" "$PLUGINS_FOLDER" || exit 1
}

install_readtags() {
	echo " - creating readtags executable"
	cd ctags
	cc -I. -DHAVE_CONFIG_H  -DREADTAGS_MAIN -o readtags readtags.c || exit 1
	echo " - adding readtags executable to $PLUGINS_FOLDER"
	cp readtags "$PLUGINS_FOLDER" || exit 1
}

# Install plugin
echo "\nInstalling Go-To Definition plug-in for Gedit 3"
mkdir -p $PLUGINS_FOLDER
install_file 'go-to-definition.plugin'
install_file 'go-to-definition.py'
install_file 'go_to_definition_helper_module.py'
install_readtags

echo '\n*** Restart gedit and enable plug-in from Preferences -> Plugins ***\n'

