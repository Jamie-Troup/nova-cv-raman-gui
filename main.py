import numpy as np
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as font
import os
import pathlib
import platform

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)
from scipy.signal import savgol_filter, find_peaks
from scipy.optimize import curve_fit
from sys import exc_info

class GraphFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.axes = None
        self.xlabel = ''
        self.ylabel = ''
        self.x = None
        self.y = None
        self.cv_num_arr = [1, 2, 5, 10, 15, 20, 25, 30, 35, 45, 50]
        self.graph_type = None
        self.filepath = None
        self.parent = parent
        self.pack_propagate(0)
        
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        toolbar = NavigationToolbar2Tk(self.canvas, self)
        
        self.canvas.get_tk_widget().pack(side='left', expand=1, fill='both')
   
    def update_view(self, tree_type, peaks=[]):
        self.figure.clear()
        self.axes = self.figure.add_subplot()
        self.graph_type = tree_type
        if self.graph_type == 'nova':
            for cv in self.cv_num_arr:
                self.axes.plot(self.x[cv-1], self.y[cv-1], label=str(cv), picker=True, pickradius=1)
                self.xlabel = 'Applied potential (V) vs. Ag'
                self.ylabel = 'Current (mA)'
        else:
            mask_1200 = np.where(self.x<1200)
            self.x = self.x[mask_1200]
            self.y = self.y[mask_1200]
            if self.y.max() > 0:
                self.y = self.y/self.y.max()
            self.axes.plot(self.x, self.y, picker=True, pickradius=1)
            self.xlabel = 'Raman shift (cm-1)'
            self.ylabel = 'Relative Intensity'
        self.axes.set_xlabel(self.xlabel, fontsize=18)
        self.axes.set_ylabel(self.ylabel, fontsize=18)
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self.parent.analysis_frame.update_view(self.cv_num_arr, tree_type, peaks)
        
    def get_cv_num_str(self, cv_num_arr):
        cv_num_str = ''
        range_start_ind = -1
        count = 0
        for x in cv_num_arr:
            if (count + 1) < len(cv_num_arr): 
                next_neighbour = ((cv_num_arr[count+1] - x) == 1)
            else:
                next_neighbour = False
            if range_start_ind > -1:
                if not next_neighbour:
                    cv_num_str = cv_num_str+' '+str(cv_num_arr[range_start_ind])+'-'+str(x)+','
                    range_start_ind = -1
            else:
                if next_neighbour:
                    range_start_ind = count
                else:
                    cv_num_str = cv_num_str + ' ' + str(x) + ','   
            count+=1
        return cv_num_str
        
    def get_cv_num_array(self, cv_num_str):
        array = []
        split_str = cv_num_str.split(',')
        for string in split_str:
            string = string.strip()
            if string:
                if '-' in string:
                    split_str = string.split('-')
                    if split_str[0] > split_str[1]:
                        raise Exception("Repeated CV numbers or malformed cv number input")
                    for val in range(int(split_str[0]), int(split_str[1])+1):
                        array.append(val)
                else:
                    array.append(int(string))
        repeat_vals = 0
        for x in array:
            if array.count(x) > 1:
                repeat_vals = 1
        if repeat_vals:
            raise Exception("Repeated CV numbers or malformed cv number input")
        else:
            return array


class NovaFrame(ttk.Frame):
    def __init__(self, parent, graph_frame, cv_num_arr, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs) 
        self.graph_frame = graph_frame
        self.parent = parent
        
        self.cont = tk.Frame(self)
        self.header_frame = tk.Frame(self.cont)
        self.header = tk.Label(self.header_frame, text='CV numbers')
        self.cv_num_str_var = tk.StringVar(value=self.graph_frame.get_cv_num_str(cv_num_arr))
        self.cv_entry_frame = tk.Frame(self.cont)
        self.cv_entry_frame.rowconfigure(0, weight=1)
        self.cv_entry_frame.columnconfigure(0, weight=1)
        self.cv_num_entry = tk.Entry(self.cv_entry_frame, textvariable=self.cv_num_str_var)
        self.sub_btn_frame = tk.Frame(self.cont)
        self.submit_btn = Button(self.sub_btn_frame, text='Submit')
        self.submit_btn.configure(command=self.update_cvs)
        # Legend
        self.legend_cont = tk.Frame(self)
        self.legend_header = tk.Label(self.legend_cont, text='Legend')
        self.legend_grid_cont = tk.Frame(self.legend_cont)
        self.legend_grid_cont.rowconfigure(0, weight=1)
        self.legend_grid_cont.columnconfigure(0, weight=1)
        self.legend_canv = tk.Canvas(self.legend_grid_cont)
        self.vert_scrollbar = ttk.Scrollbar(self.legend_grid_cont, orient='vertical', command=self.legend_canv.yview)
        self.legend_canv.configure(yscrollcommand=self.vert_scrollbar.set)
        self.scroll_frame = tk.Frame(self.legend_canv)
        self.scroll_frame.bind('<Configure>', lambda e: self.legend_canv.configure(scrollregion=self.legend_canv.bbox('all')))
        self.legend_canv.create_window((0,0), window=self.scroll_frame, anchor='nw', tags='scroll_frame')
        self.legend_canv.bind('<Configure>', self.resize_scroll_frame)
       
        legend = {'handles': [], 'labels': []}       
        axes = graph_frame.figure.axes[0]
        legend['handles'],legend['labels'] = axes.get_legend_handles_labels()
        index = 0
        for handle in legend['handles']:
            label = legend['labels'][index]
            self.add_legend(handle, label)
            index+=1
                    
        self.cont.pack(side='left', padx=(10,0), expand=1, fill='both')
        self.header_frame.pack(expand=1, fill='both')
        self.header.pack(side='bottom')
        self.cv_entry_frame.pack(expand=1, fill='both')
        self.cv_num_entry.grid(row=0, column=0)
        self.sub_btn_frame.pack(expand=1, fill='both')
        self.submit_btn.pack(side='top')
        self.legend_header.pack(expand=1, fill='x')
        self.legend_grid_cont.pack(expand=1, fill='both')
        self.vert_scrollbar.grid(row=0, column=1, sticky='ns')
        self.legend_canv.grid(row=0, column=0)
        if len(cv_num_arr) > 1:
            self.legend_cont.pack(side='left', expand=1, fill='both')
    
    def resize_scroll_frame(self, event):
        self.legend_canv.itemconfig("scroll_frame", width=event.width)
    
    def add_legend(self, handle, label):
        frame = tk.Frame(self.scroll_frame)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        label = tk.Label(frame, text=label)
        colour = tk.Label(frame, text='        ', bg=handle.get_color())
                
        frame.pack(fill='x', expand=1)
        label.grid(row=0, column=0, pady=(0,5))
        colour.grid(row=0, column=1, pady=(0,5), padx=(0,10))
        
    def update_cvs(self):
        old_cv_num_arr = self.graph_frame.cv_num_arr
        try:
            self.submit_btn.config(bg=self.submit_btn.btn_col)
            self.submit_btn.config(activebackground=self.submit_btn.active_bg_col)
            self.graph_frame.cv_num_arr = self.graph_frame.get_cv_num_array(self.cv_num_str_var.get())
            self.graph_frame.update_view('nova')
        except Exception as e:
            self.submit_btn.config(bg='red', activebackground='darkred', text='Error')
            self.parent.save_frame.save_btn.config(state='disabled')
            print(e)
        
        
class AnalysisFrame(ttk.Frame):
    def __init__(self, parent, graph_frame, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.pack_propagate(0)
        self.no_content = tk.Label(self, text='- Holding -')
        self.graph_frame = graph_frame
        self.peak_sel_frame = None
        
        self.no_content.pack(fill='both', expand=True)
        
    def update_view(self, cv_num_arr, tree_type, peaks):
        self.clear()
        if tree_type == 'raman':
            self.load_peak_analysis(peaks)
        else:
            self.load_nova_analysis(cv_num_arr)
            if len(cv_num_arr) == 1:
                self.load_peak_analysis(peaks)
        self.load_save_section()
            
    def load_peak_analysis(self, peaks):
        self.peak_sel_frame = PeakSelectFrame(self, self.graph_frame)
        for peak in peaks:
            self.peak_sel_frame.add_peak(peak)
        self.peak_sel_frame.pack(side='left', expand=1, fill='both')
            
    def load_nova_analysis(self, cv_num_arr):  
        self.nova_frame = NovaFrame(self, self.parent.graph_frame, cv_num_arr)
        self.nova_frame.pack(side='left', expand=1, fill='both')
        
    def load_save_section(self):
        self.save_frame = SaveFrame(self, self.graph_frame)
        self.save_frame.pack(side='left', expand=1, fill='both')
            
    def clear(self):
        for child in self.winfo_children():
            child.destroy()


class SaveFrame(ttk.Frame):
    def __init__(self, parent, graph_frame, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.graph_frame = graph_frame
        
        self.save_btn = Button(self, text='Save')
        self.save_btn.config(command=self.save)
        self.save_btn.pack()
        
    def save(self):
        filepath = self.graph_frame.filepath
        split_filepath = filepath.split('/')
        count = 0
        for x in split_filepath:
            if x == 'data':
                split_filepath[count] = 'saved_data'
            count+=1
        save_filepath = '/'.join(split_filepath)
        save_check = 0
        if self.graph_frame.graph_type == 'nova':
            tree = self.parent.parent.saved_nova_tree
            if len(self.graph_frame.cv_num_arr) > 1:
                split_filepath = save_filepath.split('.')
                save_filepath = split_filepath[0] + '_CVs.' + split_filepath[-1]
                save_check = 1
        else:
            tree = self.parent.parent.saved_ram_tree
        if self.parent.peak_sel_frame:
            # loop through and check if any peak frames have peaks
            peak_dicts = []
            for peak_frame in self.parent.peak_sel_frame.peak_frames:
                if peak_frame.peak_dict['peak_val'] != 'N/A':
                    peak_dicts.append(peak_frame.peak_dict)
                    save_check = 1
        if save_check:
            split_filepath = save_filepath.split('/')
            dir_filepath = '/'.join(split_filepath[0:len(split_filepath)-1])
            if not os.path.exists(dir_filepath):
                os.makedirs(dir_filepath)
            with open(save_filepath, 'w') as f:
                f.truncate()
                f.write('filepath;'+filepath+'\n')
                if self.parent.peak_sel_frame:
                    for x in peak_dicts:
                        f.write('bound_1;'+str(x['bound_1'])+"\n")
                        f.write('bound_2;'+str(x['bound_2'])+"\n")
                        f.write('peak_val;'+str(x['peak_val'])+"\n")
                if self.graph_frame.graph_type == 'nova':
                    cv_num = self.graph_frame.cv_num_arr
                    cv_num_str = self.graph_frame.get_cv_num_str(cv_num)
                    f.write('cvNumberStr;'+cv_num_str+"\n")
                self.save_btn.config(bg=self.save_btn.btn_col, activebackground=self.save_btn.active_bg_col)
            tree.check_tree_items_in_sys()
        else:
            if os.path.isfile(save_filepath):
                if self.parent.peak_sel_frame.peak_frames:
                    self.save_btn.config(bg='red', activebackground='darkred')
                else:    
                    filepath_list, item_ids = tree.get_tree_item_lists()
                    item_id = self.filepath_to_item_id(save_filepath, filepath_list, item_ids)
                    tree.delete_tree_item(save_filepath, item_id, True)
                    p = pathlib.Path(save_filepath)
                    count = 0
                    parent = (str(p.parents[count]).split('/'))[-1]
                    while parent != 'raman' and parent != 'nova':
                        parent_filepath = p.parents[count]
                        if len(list(parent_filepath.iterdir())) == 0:
                            item_id = self.filepath_to_item_id(str(parent_filepath), filepath_list, item_ids)
                            tree.delete_tree_item(str(parent_filepath), item_id, True)
                            count+=1
                            parent = (str(p.parents[count]).split('/'))[-1]
                        else:
                            parent = 'raman'
                    tree.check_tree_items_in_sys()
            else:
                self.save_btn.config(bg='red', activebackground='darkred')
    
    def filepath_to_item_id(self, filepath, filepath_list, item_ids):
        count = 0
        for x in filepath_list:
            if x == filepath:
                return item_ids[count]
            count+=1
                

class PeakSelector(ttk.Frame):
    def __init__(self, parent, peak, peak_num, peak_select_frame, graph_frame,*args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.peak_select_frame = peak_select_frame
        self.peak_dict = peak
        self.number = peak_num
        self.graph_frame = graph_frame
        self.cid_list = []
        self.clicked_bound = None
        if peak:
            bound_1_ind = int(peak['bound_1'])
            bound_2_ind = int(peak['bound_2'])
            x,y = self.graph_frame.x, self.graph_frame.y
            if self.graph_frame.graph_type == 'nova':
                cv_num = self.graph_frame.cv_num_arr[0]
                bound_1 = tk.IntVar(value=round(x[cv_num-1][bound_1_ind],2))
                bound_2 = tk.IntVar(value=round(x[cv_num-1][bound_2_ind],2))
            else:
                bound_1 = tk.IntVar(value=round(x[bound_1_ind],2))
                bound_2 = tk.IntVar(value=round(x[bound_2_ind],2))
            peak_val = round(float(peak['peak_val']), 2)
        else:
            bound_1 = tk.IntVar(value = '  -  ')
            bound_2 = tk.IntVar(value = '  -  ')
            peak_val = 'N/A'
            self.peak_dict = {'peak_num': self.number, 'bound_1': -2, 'bound_2': -2, 'peak_val': 0}
            
        self.bound_1_val_label = tk.Label(self, textvariable=bound_1, name='bound_1', bg='white')
        self.bound_2_val_label = tk.Label(self, textvariable=bound_2, name='bound_2', bg='white')
        self.peak_val_label = tk.Label(self, text=peak_val, name='peak_val', bg='lightblue')
        bound_1_label = tk.Label(self, text='Bound 1 ')
        bound_2_label = tk.Label(self, text=' Bound 2 ')
        peak_label = tk.Label(self, text=' Peak ')
        delete_btn = tk.Button(self, text='Delete')
        delete_btn.configure(command=self.delete_peak_sel)
        
        self.bound_1_val_label.bind('<ButtonPress-1>', self.on_bound_click)
        self.bound_2_val_label.bind('<ButtonPress-1>', self.on_bound_click)
        
        bound_1_label.pack(side='left')
        self.bound_1_val_label.pack(side='left')
        bound_2_label.pack(side='left')
        self.bound_2_val_label.pack(side='left')
        peak_label.pack(side='left')
        self.peak_val_label.pack(side='left')
        delete_btn.pack(side='left', padx=(5, 0))
        
    def delete_peak_sel(self):
        self.destroy()
        del self.peak_select_frame.peak_frames[self.number]
        del self
        
    def check_graph_click(self, event, colour, bound_widget):
        master = event.widget.master
        if master.winfo_name() != 'graph_frame':
            if bound_widget.winfo_name() == self.clicked_bound:
                for cid in self.cid_list:
                    self.graph_frame.canvas.mpl_disconnect(cid)
                self.graph_frame.master.parent.unbind('<ButtonPress-1>')
            bound_widget.configure(bg=colour)
        
    def on_bound_click(self, event):
        self.graph_frame.master.parent.unbind('<ButtonPress-1>')
        bound_widget = event.widget
        self.clicked_bound = bound_widget.winfo_name()
        col = bound_widget['bg']
        self.graph_frame.master.parent.bind('<ButtonPress-1>', lambda e: self.check_graph_click(e, col, bound_widget))
        ax = self.graph_frame.figure.axes[0]
        for cid in self.cid_list:
            self.graph_frame.canvas.mpl_disconnect(cid)
        cid = self.graph_frame.canvas.mpl_connect('pick_event', lambda e: self.on_graph_click(e, bound_widget, cid))
        self.cid_list.append(cid)
        bound_widget.config(bg='yellow')
        
    def on_graph_click(self, graph_event, bound_wid, cid):
        line = graph_event.artist
        x = line.get_xdata()
        y = line.get_ydata()
        ind = graph_event.ind[0]
        point = tk.IntVar(value=round(x[ind],2))
        bound_wid.config(textvariable=point, bg='white')
        self.graph_frame.canvas.mpl_disconnect(cid)
        self.graph_frame.master.parent.unbind('<ButtonPress-1>')
        if self.peak_dict['peak_num'] == self.number:
            name = bound_wid.winfo_name()
            if name == 'bound_1':
                self.peak_dict['bound_1'] = ind
            else:
                self.peak_dict['bound_2'] = ind
            if (self.peak_dict['bound_1'] != -2) and (self.peak_dict['bound_2'] != -2):
                 bound_1_ind = self.peak_dict['bound_1']
                 bound_2_ind = self.peak_dict['bound_2']
                 try:
                     # set save button to default colours
                     peak_inds = [bound_1_ind, bound_2_ind]
                     peak_inds.sort()
                     peak = self.peak_fit(x, y, peak_inds, self.graph_frame.graph_type)
                     self.peak_dict['peak_val'] = peak
                     self.peak_val_label.config(text=round(peak,2), bg='lightblue')
                 except Exception as e:
                     self.peak_val_label.config(bg='red', text='N/A')
                     self.peak_dict['peak_val'] = 'N/A'
                     exc_type, exc_obj, tb = exc_info()
                     line_no = tb.tb_lineno
                     filename = tb.tb_frame.f_code.co_filename
                     print('{}, line {}, file {}'.format(e, line_no, filename))
            
    def lorentz_eqn(self, x, amp, width, centre):
	    return amp*((width/2)/((x-centre)**2 + (width/2)**2))
	
    def gaussian_eqn(self, x, amp, width, centre):
	    return amp*np.exp(-0.5*np.square((x-centre)/width))
    
    def peak_fit(self, x, y, peak_inds, graph_type):
        x_data = x[peak_inds[0]:peak_inds[1]]
        y_data = y[peak_inds[0]:peak_inds[1]]
        width_guess = abs(x_data[0]-x_data[-1])
        centre_guess = (x_data[0]+x_data[-1])/2
        p0 = [1, width_guess, centre_guess]
        if graph_type == 'raman':
            function = self.lorentz_eqn
        else:
            function = self.gaussian_eqn
        if y_data[0] >= max(y_data):
            y_data = y_data*-1
        curve_params = curve_fit(function, x_data, y_data, p0=p0)[0]
        x_data = np.linspace(x_data[0], x_data[-1], 1000)
        ideal_y = function(x_data, curve_params[0], curve_params[1], curve_params[2])
        peak_ind = find_peaks(ideal_y)[0][0]
        return x_data[peak_ind]
        
            
class PeakSelectFrame(ttk.Frame):
    def __init__(self, parent, graph_frame, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.parent = parent
        self.peak_frames = []
        self.graph_frame = graph_frame
        
        self.peak_header = tk.Label(self, text='Peaks')
        self.canvas = tk.Canvas(self)
        self.vert_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vert_scrollbar.set)
        self.scroll_frame = tk.Frame(self.canvas)
        self.scroll_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor='nw', tags='scroll_frame')
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure('scroll_frame', width=e.width))
        
        self.new_peak_btn_cont = tk.Frame(self.scroll_frame)
        self.new_peak_btn = Button(self.new_peak_btn_cont, text='- New Peak -')
        self.new_peak_btn.configure(command=lambda peak=[]: self.add_peak(peak))
        
        self.peak_header.grid(row=0, column=0)
        self.canvas.grid(row=0, column=0, sticky='nesw')
        self.vert_scrollbar.grid(row=0, column=1, sticky='ns')
        self.new_peak_btn_cont.pack(side='bottom')
        self.new_peak_btn.pack()
            
    def add_peak(self, peak):
        new_peak = PeakSelector(self.scroll_frame, peak, len(self.peak_frames), self, self.graph_frame)
        new_peak.pack()
        self.peak_frames.append(new_peak)
           
                      
class Button(tk.Button):
    def __init__(self, parent, *args, **kwargs):
        tk.Button.__init__(self, parent, *args, **kwargs)
        
        self.active_bg_col = self['activebackground']
        self.btn_col = self['bg']
        
        
class TreeviewFrame(tk.Frame):
    def __init__(self, parent, tree_type, root_path, header, save_tree=False, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.tree_type = tree_type
        self.save_tree = save_tree
        self.root_path = root_path
        self.pack_propagate(0)
        
        self.font = font.nametofont('TkDefaultFont')
        self.custom_indent = 15
        self.arrow_width = 20
        style = ttk.Style()
        style.configure('Treeview', indent=self.custom_indent)
        
        self.frame = tk.Frame(self)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.frame, highlightthickness=0, bg='white')
        self.canvas.bind('<Configure>', self.set_scroll_frame_dim)
        self.scroll_frame = ttk.Frame(self.canvas)
        self.tree = ttk.Treeview(self.scroll_frame)
        self.tree.heading('#0', text=header, anchor='w')
        self.vert_scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vert_scrollbar.set)
        self.hori_scrollbar = ttk.Scrollbar(self.frame, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hori_scrollbar.set)
        self.scroll_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.refresh_menu = tk.Menu(self.tree, tearoff=0)
        self.refresh_menu.add_command(label='Refresh', command=self.check_tree_items_in_sys)
        self.refresh_menu.bind('<FocusOut>', lambda event, menu=self.refresh_menu: self.menu_lose_focus(event, menu))
        self.delete_menu = tk.Menu(self.tree, tearoff=0)    
        self.delete_menu.bind('<FocusOut>', lambda event, menu=self.delete_menu: self.menu_lose_focus(event, menu))
                
        self.tree.bind('<<TreeviewSelect>>', self.toggle_row_expansion)
        self.tree.bind('<Button-3>', self.show_refresh_menu)
        self.tree.bind('<Motion>', self.highlight_row)
        self.tree.tag_bind('file', '<<TreeviewSelect>>', self.open_graph)
        self.tree.tag_configure('highlight', background='lightblue')
        self.populate_tree('', self.root_path)
        
        self.frame.pack(expand=1, fill='both')
        self.canvas.grid(row=0, column=0, sticky='nesw')
        self.vert_scrollbar.grid(row=0, column=1, sticky='ns')
        self.hori_scrollbar.grid(row=1, column=0, sticky='ew')
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor='nw', tags='scrollable_frame')
        self.tree.pack(expand=1, fill='both')
        
    def menu_lose_focus(self, event, menu):
        menu.unpost()
    
    def show_refresh_menu(self, event):
        region = self.tree.identify('region', event.x, event.y)
        if region == 'heading':
            self.delete_menu.unpost()
            self.refresh_menu.tk_popup(event.x_root, event.y_root)
            self.refresh_menu.focus_set()
        else:
            self.refresh_menu.unpost()
            item_id = self.tree.identify('item', event.x, event.y)
            filepath = self.tree.item(item_id)['tags'][1]
            self.delete_menu.delete(0, 'end')
            self.delete_menu.add_command(label='Delete', command=lambda: self.delete_tree_item(filepath, item_id, True))
            self.delete_menu.tk_popup(event.x_root, event.y_root)
            self.delete_menu.focus_set()
        self.refresh_menu.grab_release()
    
    def set_scroll_frame_dim(self, event):
        self.canvas.update()
        self.canvas.itemconfigure('scrollable_frame', width=self.canvas.winfo_width(), height=self.canvas.winfo_height())
        
    def get_indent_lvl(self, item_id):
        indent_lvl = 0
        parent_id = self.tree.parent(item_id)
        while parent_id:
            indent_lvl += 1
            parent_id = self.tree.parent(parent_id)
        return indent_lvl
    
    def toggle_row_expansion(self, event):
        if self.tree.selection(): # When deleting a selected item from treeview it fires, yet there is no longer a selected item, so this is needed
            item_id = self.tree.selection()[0]
            cursor_local_pos =  (self.tree.winfo_pointerx() - self.tree.winfo_rootx(), self.tree.winfo_pointery() - self.tree.winfo_rooty()) 
            if self.tree.identify_element(*cursor_local_pos) != 'Treeitem.indicator':
                open_state = self.tree.item(item_id, 'open')
                self.tree.item(item_id, open=not self.tree.item(item_id, 'open'))
                if open_state == 1:
                    self.sibling_width_check()
                else:
                    self.children_width_check()
            
    def children_width_check(self):
        item_id = self.tree.selection()[0]
        child_item_ids = self.tree.get_children(item_id)
        child_widths = []
        for id in child_item_ids:
            item = self.tree.item(id)
            child_width = int(self.font.measure(item['text'])) + 30
            indent_lvl = self.get_indent_lvl(id)
            if 'folder' in item['tags']:
                child_width += self.arrow_width
            else:
                child_width += self.custom_indent
            child_width += self.arrow_width * indent_lvl
            child_widths.append(child_width)
        col_width = self.tree.column('#0')['width']
        if child_widths:
            if max(child_widths) > col_width:
                self.canvas.itemconfigure('scrollable_frame', width=max(child_widths))
                    
    def sibling_width_check(self):
        item_id = self.tree.selection()[0]
        sibling_item_ids = self.tree.get_children(self.tree.parent(item_id))
        indent_lvl = self.get_indent_lvl(item_id)
        sibling_widths = []
        for id in sibling_item_ids:
            item = self.tree.item(id)
            sibling_width = int(self.font.measure(item['text'])) + 30
            if 'folder' in item['tags']:
                sibling_width += self.arrow_width
            else:
                sibling_width += self.custom_indent
            sibling_width += self.arrow_width * indent_lvl
            sibling_widths.append(sibling_width)
        if max(sibling_widths) > self.canvas.winfo_width():                                         
            self.canvas.itemconfigure('scrollable_frame', width=max(sibling_widths))
        else:
            self.canvas.itemconfigure('scrollable_frame', width=self.canvas.winfo_width())
            
    def highlight_row(self, event):
        item = self.tree.identify_row(event.y)
        self.tree.tk.call(self.tree, "tag", "remove", "highlight")
        self.tree.tk.call(self.tree, "tag", "add", "highlight", item)
            
    def populate_tree(self, parent, root_path):
        for filepath in os.listdir(root_path):
            abs_path = os.path.join(root_path, filepath)
            is_dir = os.path.isdir(abs_path)
            if not is_dir:
                split_filepath = filepath.split('.')
                if split_filepath[-1] == 'txt':
                    filename = '.'.join(split_filepath[0:-1])
                    oid = self.tree.insert(parent, 'end', text=filename, open=False, tags=('file', abs_path))
            else:
                oid = self.tree.insert(parent, 'end', text=filepath, open=False, tags=('folder', abs_path))
                self.populate_tree(oid, abs_path)
            
    def open_graph(self, event):
        item_id = self.tree.selection()[0]
        filepath = self.tree.item(item_id)['tags'][1]
        peaks = []
        if self.save_tree:
            filepath, cv_num_str, peaks = self.open_save(filepath)
            if self.tree_type == 'nova':
                self.parent.graph_frame.cv_num_arr = self.parent.graph_frame.get_cv_num_array(cv_num_str)
        else:
            self.parent.graph_frame.cv_num_arr = [1, 2, 5, 10, 15, 20, 25, 30, 35, 45, 50]            
        x,y = self.process_file(filepath, self.tree_type)
        y = savgol_filter(y, window_length=11, polyorder=3, mode="nearest")
        self.parent.graph_frame.x,self.parent.graph_frame.y = x,y
        self.parent.graph_frame.update_view(self.tree_type, peaks)
        self.parent.graph_frame.filepath = filepath
            
    def open_save(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines= f.read().splitlines()
            peaks = []
            cv_num_str = ''
            og_filepath = ''
            count = 0
            for line in lines:
                split_line = line.split(';')
                if split_line[0] == 'filepath':
                    og_filepath = split_line[1]
                if split_line[0] == 'bound_1':
                    peaks.append({'bound_1':split_line[1], 'bound_2':'', 'peak_val':''})
                if split_line[0] == 'bound_2':
                    peaks[count]['bound_2'] = split_line[1]
                if split_line[0] == 'peak_val':
                    peaks[count]['peak_val'] = split_line[1]
                    count+=1
                else:
                    cv_num_str = split_line[1]
        return og_filepath, cv_num_str, peaks
             
    def process_file(self, filepath, tree_type):
        with open(filepath, 'r', encoding="utf-8") as f:
            if tree_type == 'raman':
                f.seek(len(f.readline()) + 1)
            else:
                first_line = f.readline()
                headers = first_line.split(';')
                count=pot_app_ind=current_ind=scan_ind=0
                for header in headers:
                    if header == 'Potential applied (V)':
                        pot_app_ind = count
                    elif header == 'WE(1).Current (A)':
                        current_ind = count
                    elif header == 'Scan':
                        scan_ind = count
                    count += 1
            lines = f.readlines()
            x = []
            y = []
            for line in lines:
                if tree_type == 'raman':
                    split = line.split('\t')
                    x.insert(0, float(split[0]))
                    y.insert(0, float(split[1])) 
                else:
                    vals = line.split(';')
                    pot_app = float(vals[pot_app_ind])
                    current = float(vals[current_ind])
                    if scan_ind:
                        scan = int(vals[scan_ind])
                        if len(x) < scan:
                            x.append([])
                            y.append([])
                        x[scan-1].append(pot_app)
                        y[scan-1].append(current)   
                    else:
                        x.append(pot_app)
                        y.append(current)
        return np.array(x),np.array(y)
    
    def get_all_children(self, item=''):
        children = self.tree.get_children(item)
        for child in children:
            children+=self.get_all_children(child)
        return children
    
    def get_tree_item_lists(self):
        item_ids = list(self.get_all_children())
        filepath_list = []
        for item_id in item_ids:
            filepath_list.append(self.tree.item(item_id)['tags'][1])
        return filepath_list, item_ids
        
    def check_tree_items_in_sys(self):
        parent = ''
        filepath_list, item_ids = self.get_tree_item_lists()
        count = 0
        for filepath in filepath_list:
            path = pathlib.Path(filepath)
            if not path.exists():
                item_id = item_ids[count]
                self.delete_tree_item(filepath, item_id)
            count+=1
        self.check_sys_in_tree('', self.root_path, filepath_list, item_ids)
    
    def check_sys_in_tree(self, parent, root_path, filepath_list, item_ids):
    	for p in os.listdir(root_path):
		    abs_path = os.path.join(root_path, p)
		    is_dir = os.path.isdir(abs_path)
		    if not is_dir:
			    split_filepath = p.split('.')
			    filepath_no_ext = split_filepath[0]
			    if abs_path not in filepath_list:
				    oid = self.tree.insert(parent, 'end', text=filepath_no_ext, open=False, tags=('file', abs_path))
				    self.tree.tag_bind(oid, '<Motion>', self.highlight_row)
		    else:
			    if abs_path not in filepath_list:
				    oid = self.tree.insert(parent, 'end', text=p, open=False, tags=('folder', abs_path))
				    self.tree.tag_bind(oid, '<Motion>', self.highlight_row)
				    self.check_sys_in_tree(oid, abs_path, filepath_list, item_ids)
			    else:
				    oid = item_ids[filepath_list.index(abs_path)]
				    self.check_sys_in_tree(oid, abs_path, filepath_list, item_ids)
				    
    def delete_tree_item(self, filepath, item_id=None, del_from_sys=False):
        if item_id:
            if self.tree.exists(item_id):
                self.tree.delete(item_id)
        if del_from_sys:
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                else:
                    for x in os.listdir(filepath):
                        self.delete_tree_item(filepath+'/'+x, del_from_sys=True)
                    os.rmdir(filepath)
            except Exception as e:
                exc_type, exc_obj, tb = exc_info()
                line_no = tb.tb_lineno
                filename = tb.tb_frame.f_code.co_filename
                print('{}, line {}, file {}'.format(e, line_no, filename))

            
class MainApp(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        
        self.parent = parent # this is root, self is a frame in root
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        
        self.graph_frame = GraphFrame(self, name='graph_frame')
        self.analysis_frame = AnalysisFrame(self, self.graph_frame)
        raman_datapath = os.getcwd() + '/data/raman'
        self.raman_tree = TreeviewFrame(self, 'raman', raman_datapath, 'Raman')
        nova_datapath = os.getcwd() + '/data/nova'
        self.nova_tree = TreeviewFrame(self, 'nova', nova_datapath, 'Nova')
        saved_ram_datapath = os.getcwd() + '/saved_data/raman'
        self.saved_ram_tree = TreeviewFrame(self, 'raman', saved_ram_datapath, 'Saved Raman', True)
        saved_nova_datapath = os.getcwd() + '/saved_data/nova'
        self.saved_nova_tree = TreeviewFrame(self, 'nova', saved_nova_datapath, 'Saved Nova', True)
        
        # Pack/Grid statements
        self.graph_frame.grid(column=2, row=0, rowspan=3, columnspan=3, sticky='nesw')
        self.analysis_frame.grid(column=2, row=3, columnspan=3, sticky='nesw')
        self.raman_tree.grid(column=1, row=0, rowspan=2, sticky='nesw')
        self.nova_tree.grid(column=0, row=0, rowspan=2, sticky='nesw')
        self.saved_ram_tree.grid(column=1,row=2,rowspan=2,sticky='nesw')
        self.saved_nova_tree.grid(column=0, row=2, rowspan=2, sticky='nesw')
        
if __name__ == '__main__':
    root = tk.Tk()
    if platform.system == 'Windows':
        root.state('zoomed')
    else:
        root.attributes('-zoomed', True)
    MainApp(root).pack(fill='both', expand=True)
    root.mainloop()
