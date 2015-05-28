from gi.repository import Gtk, Gedit, Gdk, GObject
import re

def get_start_index(word, text):
	#Get offset of word in text
	pos = re.search(r"\b" + word + r"\b", text).start()
	return pos

def get_headers_for_c_file(doc):
	# Returns a list of user headers in a C code
	begin = doc.get_start_iter()
	end = doc.get_end_iter()
	text = doc.get_text(begin, end, False)
	header_list = re.findall("#include\\s*\"([^\"]+)\"", text)
	return header_list	
	
def get_proper_path(path):
	#Convert uri to unix like path notation
	ret = path
	ret = ret.replace('(', '\\(')
	ret = ret.replace(')', '\\)')
	ret = ret.replace(' ', '\\ ')
	return ret

def extract_attributes(data):
	#Returns [path, line, column] values
	line = re.findall('line:(\d+)', data)
	line = int(line[0])
	def_stmt = re.findall('/\^([^\$]+)\$/;"', data)
	def_stmt = def_stmt[0]
	tokens = data.split('\t')
	col = get_start_index(tokens[0], def_stmt)
	return [tokens[1], line, col, def_stmt]

def process_result(result):
	result = result.decode()
	result = result.split('\n')
	result.pop()
	tag_data = []
	for item in result:
		tag_data.append(extract_attributes(item))
	return tag_data
		
class CLangProcessing(object):
	
	def __init__(self, doc, result):
		self.doc_uri = doc.get_uri_for_display()
		self.header_path = self.doc_uri.replace(doc.get_short_name_for_display(), '')
		self.headers = get_headers_for_c_file(doc)
		self.result = result
	
	def get_match(self):
		selected = []
		if len(self.result) == 1:
			return self.result[0], False
		
		if len(self.result) > 1:
			paths = 0
			#If more than one matching tag belongs to
			#the same file then return nothing as 
			#matching need not be performed
			for row in self.result:
				if row[0] in self.doc_uri:
					paths += 1
			
			if paths > 1:
				return [], True
			
			#Else find the right match and return
			#that row
			for row in self.result:
				if row[0] in self.doc_uri:
					return row, False
				else:
					for item in self.headers:
						if row[0] in self.header_path + item:
							return row, False

class TreeViewWithColumn(Gtk.TreeView):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for i, head in enumerate(['File', 'Line', 'Column', 'Definition Statement']):
			col = Gtk.TreeViewColumn(head, Gtk.CellRendererText(), text=i)
			self.append_column(col)

class MatchWindow(Gtk.Window):
	def __init__(self, title, records, opener, doc):
		Gtk.Window.__init__(self)
		self.treeview = TreeViewWithColumn(model=Gtk.ListStore(str, int, int, str))
		self.connect("key-press-event", self.key_enter)
		self.connect("button-press-event", self.key_enter)
		sw = Gtk.ScrolledWindow()
		sw.add(self.treeview)
		for record in records:
			if record is not None:
				self.treeview.get_model().append(record)
		self.add(sw)
		self.title = title
		self.doc = doc
		self.opener = opener
		self.set_title("Matches for '" + title + "'")
		self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
		self.set_modal(True)
		self.set_size_request(440, 320)
		
	def key_enter(self, window, event):
		e_type = event.get_event_type()
		if (e_type == Gdk.EventType._2BUTTON_PRESS or 
			(e_type == Gdk.EventType.KEY_PRESS and event.keyval == Gdk.KEY_Return)):
			model, tree_itr = self.treeview.get_selection().get_selected()
			selected = model.get(tree_itr, 0, 1, 2, 3)
			self.destroy()
			self.opener(self.title, self.doc, selected)
		
		
		
		
		
