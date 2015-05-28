# Copyright (C) 2015 - Pallab Pain <pallabkumarpain@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gedit
from gi.repository import GObject

import os
import re
import subprocess
import go_to_definition_helper_module as helper

valid_chars = list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_')

GEDIT_PLUGINS_FOLDER = '/.local/share/gedit/plugins'
READTAGS_PATH = os.path.expanduser('~') + GEDIT_PLUGINS_FOLDER

MENU_ACTIONS = [
	("select-folder", "Select Root Folder", "<Ctrl><Alt>o"),
	("refresh-tags", "Refresh Folder Tags", "<Ctrl><Alt>r"),
	("check-folder", "Current Root Folder", "<Ctrl><Alt>c")
]

class GoToDefAppActivatable(GObject.Object, Gedit.AppActivatable):
	app = GObject.property(type=Gedit.App)
	
	def do_activate(self):
		self.menu_ext = self.extend_menu("edit-section")
		for action, title, accel in MENU_ACTIONS:
			self.app.add_accelerator(accel, "win." + action, None)
			item = Gio.MenuItem.new(_(title), "win." + action)
			self.menu_ext.append_menu_item(item)
	
	def do_deactivate(self):
		for item in MENU_ACTIONS:
			action = "win." + item[0]
			self.app.remove_accelerator(action, None)
		self.menu_ext = None
		
	
class GoToDefinitionPlugin(GObject.Object, Gedit.WindowActivatable):
	HandlerName = 'GoToDefinitionHandler'
	window = GObject.property(type=Gedit.Window)
	
	def __init__(self):
		GObject.Object.__init__(self)
		self.root_directory = ''
		self.jump_document = None
		self.word_length = 0
		self.tag_list = []
	
	def do_activate(self):
		self.add_menu()
		self.do_update_state()
		
	def do_deactivate(self):
		for view in self.window.get_views():
			handler_id = getattr(view, self.HandlerName, None)
			if handler_id != None:
				view.disconnect(handler_id)
			setattr(view, self.HandlerName, None)
		self.remove_menu()
		
	def do_update_state(self):
		self.update_ui()
		
	def update_ui(self):
		view = self.window.get_active_view()
		document = self.window.get_active_document()
		self.highlight_definition(self.jump_document, document)
		if isinstance(view, Gedit.View) and document:
			if getattr(view, self.HandlerName, None) is None:
				handler_id = view.connect('populate-popup', self.populate_context_menu, document)
				setattr(view, self.HandlerName, handler_id)
				handler_id = view.connect('key-press-event', self.on_key_press, document)
				setattr(view, self.HandlerName, handler_id)
				handler_id = view.connect('button-press-event', self.on_button_press, document)
				setattr(view, self.HandlerName, handler_id)

	def add_menu(self):
		# Adds entries to the menu
		menu_slots = {
			"select-folder" : self.select_folder,
			"refresh-tags" : self.refresh_tags,
			"check-folder" : self.show_dir_info
		}
		
		for item in MENU_ACTIONS:
			action = Gio.SimpleAction(name=item[0])
			action.connect('activate', menu_slots[item[0]])
			self.window.add_action(action)
	
	def remove_menu(self):
		# Removes entries from the menu
		for item in MENU_ACTIONS:
			self.window.remove_action(item[0])
	
	def show_info_message(self, title, text):
		dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, title)
		dialog.format_secondary_text(text)
		dialog.run()
		dialog.destroy()
	
	def show_error_message(self, title, text):
		dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, title)
		dialog.format_secondary_text(text)
		dialog.run()
		dialog.destroy()
		
	def select_folder(self, action, dummy):
		# Displays a folder select window
		dialog = Gtk.FileChooserDialog("Select project root folder", 
		  self.window, Gtk.FileChooserAction.SELECT_FOLDER, 
		  ("Close", Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK))							
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			self.root_directory = dialog.get_filename()
			self.generate_tags()
		elif response == Gtk.ResponseType.CANCEL:
			pass
		dialog.destroy()
	
	def show_dir_info(self, action, dummy):
		# Displays the path of the current root directory
		if(self.root_directory != ''):
			self.show_info_message("Current Root Folder", self.root_directory)
		else:
			self.show_error_message("Current Root Folder", "Not yet selected.")
	
	def refresh_tags(self, action, dummy):
		self.generate_tags()
		self.show_info_message("Refresh Completed", "The tags have been updated.")
	
	def generate_tags(self):
		# Generates .tags file in the current root folder
		os.chdir(self.root_directory)
		command = ['ctags','--fields=+n-k-a-f-i-K-l-m-s-S-z-t', '--c-kinds=+dfmplstuv', '-R', '-f', '.tags']
		subprocess.Popen(command)
		command = 'grep -v ! .tags | cut -f 1 | uniq'
		output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()[0]
		output = output.decode()
		output = output.split('\n')
		output.pop()
		self.tag_list = output
		
	def highlight_definition(self, jump_doc, doc):
		# Highlights the definition in the jump_doc.
		# If jump_doc and the current doc are same
		# only then the defintion will be highlighted.
		if jump_doc != None and doc != None:
			if jump_doc.get_uri_for_display() == doc.get_uri_for_display():
				start = doc.get_iter_at_mark(doc.get_insert())
				end = start.copy()
				end.forward_chars(self.word_length)
				self.apply_text_highlight(start, end, doc)
				return True
		return False
	
	def remove_text_highlight(self, document):
		# Removes any previously created text tag
		tag = document.get_tag_table().lookup('text-highlight')
		if tag != None:
			document.get_tag_table().remove(tag)
	
	def reset_highlight_vars(self):
		self.jump_document = None
		self.word_length = 0
	
	def apply_text_highlight(self, start, end, document):
		# Highlights text between start and end iters
		self.remove_text_highlight(document)
		fg_color = '#191919'
		bg_color = '#fcfc00'
		document.create_tag('text-highlight', foreground=fg_color, background=bg_color)
		document.apply_tag_by_name('text-highlight', start, end)
		
	def belongs_to_project(self, doc):
		if self.root_directory in doc.get_uri_for_display():
			return True
		return False
	
	def get_word(self, view, doc):
		#Gets the identifier under the cursor or pointer
		if self.root_directory == '':
			return False
		if not self.belongs_to_project(doc):
			return False
		
		win = view.get_window(Gtk.TextWindowType.TEXT)
		ptr, x, y, mod = win.get_pointer()
		x, y = view.window_to_buffer_coords(Gtk.TextWindowType.TEXT, x, y);
		end = view.get_iter_at_location(x, y)
		if not end:
			end = doc.get_iter_at_mark(doc.get_insert())
		
		while end.forward_char():
			ch = end.get_char()
			if ch not in valid_chars:
				break
		start = end.copy()
		while start.backward_char():
			ch = start.get_char()
			if ch not in valid_chars:
				start.forward_char()
				break
				
		word = doc.get_text(start, end, False)
		if word not in self.tag_list:
			return False
		else:
			return word
				
	def populate_context_menu(self, view, menu, doc):
		#Add Go-to definition option to pop-up menu
		word = self.get_word(view, doc)
		if word == False:
			return False
		menu_item = Gtk.MenuItem(_("Go to definition of '%s'") % word)
		menu_item.connect('activate', self.trigger_from_popup, word, doc)
		menu_item.show()
		separator = Gtk.SeparatorMenuItem()
		separator.show()
		menu.prepend(separator)
		menu.prepend(menu_item)
		return True
	
	def trigger_from_popup(self, menu_item, word, doc):
		self.go_to_definition(word, doc)
		
	def on_key_press(self, view, event, doc):
		self.remove_text_highlight(doc)
		self.reset_highlight_vars()
		if event.keyval == Gdk.KEY_F1 and event.get_state() & Gdk.ModifierType.CONTROL_MASK:
			word = self.get_word(view, doc)
			if word == False:
				return False
			self.go_to_definition(word, doc)
			
	def on_button_press(self, view, event, doc):
		#Remove highlight if any button is pressed.
		self.remove_text_highlight(doc)
		self.reset_highlight_vars()
		
	def go_to_definition(self, word, doc):
		#Gets matches from .tags file using readtags and processes it to
		#find appropriate match. If multiple matches are found and if the
		#right one cannot be decided then a box with all options is shown.
		#Pressing ENTER on the selected one will take you to it.
		
		tagfile_uri = helper.get_proper_path(self.root_directory) + '/.tags' 
		os.chdir(READTAGS_PATH)
		command = "./readtags -e -t " + tagfile_uri + " " + word
		result = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()[0]
		
		if len(result) == 0:
			return False
			
		result = helper.process_result(result)
		selected = []
		multiple_matches = False
		if doc.get_language().get_id() == 'c':
			c_obj = helper.CLangProcessing(doc, result)
			selected, multiple_matches = c_obj.get_match()
			if not multiple_matches:
				self.location_opener(word, doc, selected)
				return True
		elif len(result) == 1:	
				selected = result[0]
				self.location_opener(word, doc, selected)
				return True
		else:
			multiple_matches = True

		if multiple_matches:
			window = helper.MatchWindow(word, result, self.location_opener, doc)
			window.show_all()
			
	def location_opener(self, word, doc, selected):
		#Opens a file (if needed) and scrolls to the definition
		#and highlights it.
		doc_uri = doc.get_uri_for_display()
		self.word_length = len(word)
		path = self.root_directory + '/' + selected[0] 
		for document in self.window.get_documents():
			if (document.get_uri_for_display() == path):
				tab = self.window.get_active_tab().get_from_document(document)
				view = tab.get_view()
				self.jump_document = document
				self.window.set_active_tab(tab)
				document.goto_line(selected[1] - 1)
				view.scroll_to_cursor()
				itr = document.get_iter_at_mark(document.get_insert())
				itr.forward_chars(selected[2])
				document.place_cursor(itr)
				if doc_uri == self.jump_document.get_uri_for_display():
					self.highlight_definition(document, doc)
				else:
					self.highlight_definition(document, document)
				self.reset_highlight_vars()
				return True
		
		tab = self.window.create_tab_from_location(Gio.file_new_for_path(path), 
		  None, selected[1], selected[2] + 1, False, True)
		self.jump_document = tab.get_document()
		return True
		
