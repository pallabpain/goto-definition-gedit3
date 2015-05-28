# Go-To Definition Plugin for Gedit 3

This plug-in will allow user to jump to the definition of the identifier selected.

Parts of this plugin are based on the work of [Masatoshi Tsushima](https://github.com/utisam/gtagJump)


## Requirements

The plugin requires `exuberant-ctags` to be installed on the system.

To install [Exuberant Ctags](http://ctags.sourceforge.net/) on Ubuntu, use the following command:
	
		sudo apt-get install exuberant-ctags

The plug-in was developed and tested for *Gedit 3.14*

## Installation

- Download the archive on your computer

- Extract the files.

- Open a terminal window and navigate to the extarcted folder.

- Type `sh install.sh` and you're good to go.

## Usage

Step. 1 - Go to the menu and click on Select Root Folder (this can be your project folder which contains all your related files)

Step. 2 - Open any file which belongs to your Root Folder (or Project folder) and right click on any identifier. If the context menu shows the Go-To Definition option, then click on it and it will take you to the definition of the identifier. Alternatively you can press <kbd>Ctrl+F1</kbd> on the identifier and it will do the same.

## Languages Supported

This plug-in supports all the languages supported by Exuberant Ctags:
But, full fledge functionality may not be available for all.
It should work well for C, Python, C++, Ruby. Although the plug-in is being tested exhaustively and it will soon work for all supported languages.
