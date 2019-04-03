#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
simpleeditor.py - Class to create a simple Tk window to edit text files
'''

from tkinter import Tk, Text, Scrollbar, Menu, messagebox, filedialog, BooleanVar, Checkbutton, Label, Entry, StringVar, Grid, Frame, Toplevel
import os, subprocess, json, string

class SimpleEditor():
    '''
    Class SimpleEditor, to open a Tk window and display/edit/save the content of a given file.
    '''
    def __init__(self, root):
        self.root = root
        self.TITLE = ''
        self.file_path = None
        self.set_title()

        frame = Frame(root)
        self.yscrollbar = Scrollbar(frame, orient="vertical")
        self.editor = Text(frame, yscrollcommand=self.yscrollbar.set)
        self.editor.pack(side="left", fill="both", expand=1)
        self.editor.config(wrap = "word", # use word wrapping
                           undo = True, # Tk 8.4
                           width = 80 )
        self.editor.focus()
        self.yscrollbar.pack(side="right", fill="y")
        self.yscrollbar.config(command=self.editor.yview)
        frame.pack(fill="both", expand=1)

        #instead of closing the window, execute a function
        root.protocol("WM_DELETE_WINDOW", self.file_quit)

        #create a top level menu
        self.menubar = Menu(root)
        #Menu item File
        filemenu = Menu(self.menubar, tearoff=0)# tearoff = 0 => can't be seperated from window
        filemenu.add_command(label="New", underline=1, command=self.file_new, accelerator="Ctrl+N")
        filemenu.add_command(label="Open...", underline=1, command=self.file_open, accelerator="Ctrl+O")
        filemenu.add_command(label="Save", underline=1, command=self.file_save, accelerator="Ctrl+S")
        filemenu.add_command(label="Save As...", underline=5, command=self.file_save_as, accelerator="Ctrl+Alt+S")
        filemenu.add_separator()
        filemenu.add_command(label="Close", underline=1, command=self.file_quit, accelerator="Ctrl+W")
        self.menubar.add_cascade(label="File", underline=0, menu=filemenu)
        # display the menu
        root.config(menu=self.menubar)

    def save_if_modified(self, event=None):
        if self.editor.edit_modified(): #modified
            response = messagebox.askyesnocancel("Document modified",
                                                 "This document has been modified. Do you want to save changes?")
                                                 #yes = True, no = False, cancel = None
            if response: #yes/save
                result = self.file_save()
                if result == "saved": #saved
                    return True
                else: #save cancelled
                    return None
            else:
                return response #None = cancel/abort, False = no/discard
        else: #not modified
            return True

    def file_new(self, event=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            self.editor.delete(1.0, "end")
            self.editor.edit_modified(False)
            self.editor.edit_reset()
            self.file_path = None
            self.set_title()


    def file_open(self, event=None, filepath=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            if filepath == None:
                filepath = filedialog.askopenfilename()
            if filepath != None  and filepath != '':
                with open(filepath, encoding="utf-8") as f:
                    fileContents = f.read()# Get all the text from file.
                # Set current text to file contents
                self.editor.delete(1.0, "end")
                self.editor.insert(1.0, fileContents)
                self.editor.edit_modified(False)
                self.file_path = filepath
                self.set_title()

    def file_save(self, event=None):
        if self.file_path == None:
            result = self.file_save_as()
        else:
            result = self.file_save_as(filepath=self.file_path)
        return result

    def file_save_as(self, event=None, filepath=None):
        if filepath == None:
            filepath = filedialog.asksaveasfilename(filetypes=(('JSON files', '*.json'),
                                                               ('Config INI files', '*.ini *.cfg'),
                                                               ('Text files', '*.txt'),
                                                               ('Python files', '*.py *.pyw'),
                                                               ('All files', '*.*'))) #defaultextension='.txt'
        try:
            with open(filepath, 'wb') as f:
                text = self.editor.get(1.0, "end-1c")
                f.write(bytes(text, 'UTF-8'))
                self.editor.edit_modified(False)
                self.file_path = filepath
                self.set_title()
                return "saved"
        except FileNotFoundError:
            print('FileNotFoundError')
            return "cancelled"

    def file_quit(self, event=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            self.root.destroy() #sys.exit(0)

    def set_title(self, event=None):
        if self.file_path != None:
            title = os.path.basename(self.file_path)
        else:
            title = "Untitled"
        self.root.title(title)

    def undo(self, event=None):
        self.editor.edit_undo()

    def redo(self, event=None):
        self.editor.edit_redo()

    def main(self, event=None):
        self.editor.bind("<Control-o>", self.file_open)
        self.editor.bind("<Control-O>", self.file_open)
        self.editor.bind("<Control-S>", self.file_save)
        self.editor.bind("<Control-s>", self.file_save)
        self.editor.bind("<Control-y>", self.redo)
        self.editor.bind("<Control-Y>", self.redo)
        self.editor.bind("<Control-Z>", self.undo)
        self.editor.bind("<Control-z>", self.undo)
        self.editor.bind("<Control-W>", self.file_quit)
        self.editor.bind("<Control-w>", self.file_quit)
        self.root.grab_set()


def launch_editor(root=None, file=None):
    '''
    Handy function to launch an editor window
    '''
    if not root:
        root = Tk()
    root.wm_state('normal')
    editor = SimpleEditor(root)
    if file:
        editor.file_open(filepath=file)
    editor.main()
    root.mainloop()


def launch_modal_editor(parent=None, file=None):
    '''
    Handy function to launch an editor window
    '''
    top = Toplevel(parent)
    top.transient(parent)
    editor = SimpleEditor(top)
    if file:
        editor.file_open(filepath=file)
    editor.main()


def main():
    launch_editor(file=__file__)


if __name__ == "__main__":
    main()
