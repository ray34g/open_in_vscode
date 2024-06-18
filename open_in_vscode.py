#!/usr/bin/env python3
# -*- coding:utf-8
# https://inkscape.gitlab.io/extensions/documentation/tutorial/index.html

"""
open_in_vscode.py
Open an text editor like VSCode, vim etc for Inkscape.

:Author: Go Ray <Go.Ray@ray34g.com>
:Date: 2024-06-16
:Version: v1.0.0
"""

import inkex
from inkex.gui import GtkApp, Window, IconView, asyncme

from lxml import etree
import os
import subprocess
import sys
import tempfile
import shutil
# import xml.etree.ElementTree as ET

class OpenInVSCode(inkex.CallExtension):

    multi_inx = True
    editor_tempdir = None

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument(
            "--action", 
            action="store",
            type=str,
            dest="action",
            default=[],
            help="Determine which process to exectute.",
            )
        pars.add_argument(
            "--command", 
            action="store",
            type=str,
            dest="command",
            default='code',
            help="Command for the editor program.",
            )
        pars.add_argument(
            "--editor-tempdir-prefix", 
            action="store",
            type=str,
            dest="editor_tempdir_prefix",
            default='inkscape-vscode-',
            help="Prefix for temprary directory.",
            )
        pars.add_argument(
            "--command-option", 
            action="store",
            type=str,
            dest="command_option",
            default='-n',
            help="Command option for the editor program.",
            )
        pars.add_argument(
            "--id", 
            action="store",
            type=str,
            dest="id",
            default='layer1',
            help="This argument will be ignored.",
            )
        pars.add_argument(
            "--remove-data-attribute", 
            action="store",
            type=bool,
            dest="remove_data_attribute",
            default=True,
            help="Remove data attribute 'data-editor-tempdir' for script node.",
            )
        pars.add_argument(
            "--remove-editor-tempdir", 
            action="store",
            type=bool,
            dest="remove_editor_tempdir",
            default=True,
            help="Remove editor temporary directory.",
            )

    def call(self, input_file, output_file):
        
        action = self.options.action
        editor_tempdir_prefix = self.options.editor_tempdir_prefix
        command = self.options.command
        command_option = self.options.command_option
        remove_data_attribute = self.options.remove_data_attribute
        remove_editor_tempdir = self.options.remove_editor_tempdir

        if action == "open":
            with open(input_file, "r", encoding="utf-8") as fhl:
            
                # 1. Create temporary directory for the editor.
                self.editor_tempdir = tempfile.mkdtemp("", editor_tempdir_prefix)

                # 2. Save script node content as "*.js" file and append temporary data attribute.
                doc = etree.parse(fhl, parser=inkex.SVG_PARSER)
                fhl.close()
                svg_root = doc.getroot()
                script_nodes = svg_root.xpath("//svg:script[not(@xlink:href)]") # get embedded script element

                if len(script_nodes) > 0:
                    # 2-1. Save script file for each nodes.
                    for node in script_nodes:
                        node.attrib['data-editor-tempdir'] = self.editor_tempdir # Add data attribute for checking updates via VSCode
                        self.create_tmp_file(node.get_id() + ".js", node.text or "// Created by Inkscape Open in VSCode Extension.\n")
                else:
                    # 2-2. Create new "script1.js" file if no script node was found.
                    # node.attrib['data-editor-tempdir'] = self.editor_tempdir
                    node = etree.Element("script")
                    node.attrib['id'] = "script1" # Create new id
                    node.attrib['data-editor-tempdir'] = self.editor_tempdir # Add data attribute for checking updates via Editor
                    svg_root.append(node)
                    self.create_tmp_file("script1.js", "// Created by Inkscape Open in VSCode Extension.\n")
                
                style_nodes = svg_root.xpath("//svg:style") # get embedded style element

                if len(style_nodes) > 0:
                    # 2-1. Save script file for each nodes.
                    for node in style_nodes:
                        node.attrib['data-editor-tempdir'] = self.editor_tempdir # Add data attribute for checking updates via VSCode
                        self.create_tmp_file(node.get_id() + ".css", node.text or "/* Created by Inkscape Open in VSCode Extension. */")
                else:
                    # 2-2. Create new "style1.css" file if no style node was found.
                    node = etree.Element("style")
                    node.attrib['id'] = "style1" # Create new id
                    node.attrib['data-editor-tempdir'] = self.editor_tempdir # Add data attribute for checking updates via Editor
                    svg_root.append(node)
                    self.create_tmp_file("style1.css", "/* Created by Inkscape Open in VSCode Extension. */")

                # 3. Save modified as "output_preview.svg" file so that we can check it out in the editor. (no changes)
                doc.write(os.path.join(self.editor_tempdir, "output_preview.svg"), pretty_print=True, encoding = "UTF-8", xml_declaration = True) # for the editor (preview after purpose)

                # 4. Open temporary directory with the editor.
                self.open_editor(command, command_option)

                # 5. Save current stream as "output.svg" file. (almost nothing changed but format)
                doc.write(output_file, pretty_print=True, encoding = "UTF-8", xml_declaration = True) # for CallExtension
            return output_file
        
        elif action == "save":
            with open(input_file, "r", encoding="utf-8") as fhl:

                doc = etree.parse(fhl, parser=inkex.SVG_PARSER)
                fhl.close()
                svg_root = doc.getroot()

                # 1. Get temporary directory path for current stream.
                dirs = list(set(svg_root.xpath('//svg:*/@data-editor-tempdir')))
                dir = dirs[0] # use firstly found data
                
                if len(dirs) > 1:
                    raise inkex.AbortExtension("Could not load file, Multiple Temporary directory were found:" + str(dirs)) # TODO: alert for degradation possibility?
                elif len(dir) > 0 and os.path.isdir(dir):
                    js_files = [ f for f in os.listdir(dir) if str(f).endswith(".js") and os.path.isfile(os.path.join(dir, f)) ]
                    css_files = [ f for f in os.listdir(dir) if str(f).endswith(".css") and os.path.isfile(os.path.join(dir, f)) ]
                    # 1-1. Get Updated Javascript files
                    for js_file in js_files:
                        js_file = os.path.join(dir, js_file)

                        with open(js_file, "r", encoding="utf-8") as fhl_js:
                            id = os.path.splitext(os.path.basename(js_file))[0].replace(" ", "_")
                            js_data = fhl_js.read()
                            fhl_js.close()

                            script_nodes = svg_root.xpath('//svg:script[@id="' + id + '"]')
                            if len(script_nodes) > 0:
                                node = script_nodes[0]
                            else:
                                node = etree.SubElement(svg_root, 'script', { "id": id }) 

                            node.text = etree.CDATA(js_data)
                            
                             # 2. Remove data attribute from script node
                            if remove_data_attribute:
                                node.pop("data-editor-tempdir")
                    # 1-2. Get Updated Stylesheet files
                    for css_file in css_files:

                        css_file = os.path.join(dir, css_file)

                        with open(css_file, "r", encoding="utf-8") as fhl_css:
                            id = os.path.splitext(os.path.basename(css_file))[0].replace(" ", "_")
                            css_data = fhl_css.read()
                            fhl_css.close()

                            style_nodes = svg_root.xpath('//svg:style[@id="' + id + '"]')
                            if len(style_nodes) > 0:
                                node = style_nodes[0]
                            else:
                                node = etree.SubElement(svg_root, 'style', { "id": id }) 

                            node.text = etree.CDATA(css_data)
                            
                             # 2. Remove data attribute from script node (Optional)
                            if remove_data_attribute:
                                node.pop("data-editor-tempdir")
                    
                    # 3. Save file content as svg node
                    doc.write(output_file, pretty_print=True, encoding = "UTF-8", xml_declaration = True) # for CallExtension
                    # 4. Remobe temporary directory (Optional)
                    if remove_editor_tempdir:
                        shutil.rmtree(dir)
                        
                    return output_file
                else:
                    print("No scripts were found.", file=sys.stderr) # TODO: alert for degradation possibility?
                    return input_file
        
    def create_tmp_file(self, file_name, textdata):
        filepath = os.path.join(self.editor_tempdir, file_name)
        file = open(filepath, 'w')
        file.write(textdata)
        file.close()
        
    def open_editor(self, command, command_option):
        p = subprocess.Popen('%s %s %s' % (command, command_option, self.editor_tempdir), shell=True)
        return_code = p.wait()
        print(return_code)

if __name__ == '__main__':
    OpenInVSCode().run()
                