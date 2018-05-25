#!/usr/bin/env python
import random
from pprint import pprint
import os

class NvdlaBaseTest(object):

    def __init__(self, project_name, generated_trace_dir, name='nvdla_base_test'):
        random.seed()
        self._name = name
        self._project_name = project_name
        self._generated_trace_dir = generated_trace_dir
        self._auto_hardware_layer_name = {}  # key:scenario, value:layer_list
        self._project_define_dict = {}
        self._register_manual_dict = {}
        self._trace_config = []
        self._is_project_define_loaded = False
        self._is_register_manual_loaded = False
        self.load_project_define_file(os.path.join(self._get_abs_path_to_tree_root(), 'outdir', self._project_name, 'spec/defs/project.py'))
        self.load_register_manual_file(os.path.join(self._get_abs_path_to_tree_root(), 'outdir', self._project_name, 'spec/manual/opendla.py'))

    def _get_ref_path_to_tree_root(self, rel_path_to_tree_root = '.'):
        ## there is a file named LICENSE, it's the marker of tree root
        tree_root_marker_path = os.path.join(rel_path_to_tree_root, 'LICENSE')
        if os.path.isfile(tree_root_marker_path) is False:
            rel_path_to_tree_root = os.path.join('..', rel_path_to_tree_root)
            rel_path_to_tree_root = self._get_ref_path_to_tree_root(rel_path_to_tree_root)
        return rel_path_to_tree_root

    def _get_abs_path_to_tree_root(self):
        return os.path.abspath(self._get_ref_path_to_tree_root())

    def is_two_list_the_same(self, list_a, list_b):
        return not(bool(set(list_a).difference(set(list_b))))

    # Do some basic validation on manual before using it
    ## 1. Block key list shall be the same between dict addr_spaces and dict registers
    def validate_manual(self):
        if self.is_two_list_the_same( self._register_manual_dict['registers'].keys(), self._register_manual_dict['addr_spaces'].keys() ) is False:
            raise Exception("NvdlaTest::validate_manual", "manual registers and addr_spaces are not the same")

    # Load project definition from file
    def load_project_define_file(self, project_define_file_path):
        self._is_project_define_loaded = True
        buffer_dict = {}
        #execfile(project_define_file_path, buffer_dict)
        exec(open(project_define_file_path).read(), buffer_dict)
        self._project_define_dict = dict(buffer_dict['PROJVAR'])
        #print(self._project_define_dict)

    # Load manual from file
    def load_register_manual_file(self, manual_file_path):
        self._is_register_manual_loaded = True
        #execfile(manual_file_path, self._register_manual_dict)
        exec(open(manual_file_path).read(), self._register_manual_dict)
        self.validate_manual()

    def reg_write(self, block, register, value):
        block_reg_name = '.'.join([block, register])
        self._trace_config.append('reg_write(%s, %s);' % (block_reg_name, hex(value)))

    def reg_read_check(self, block, register, value):
        block_reg_name = '.'.join([block, register])
        read_mask      = self._register_manual_dict['registers'][block][register]['read_mask']
        self._trace_config.append('reg_read_check(%s, %s);' % (block_reg_name, hex(value&read_mask)))

    def sync_notify(self, block, event_name):
        self._trace_config.append('sync_notify(%s, %s);' % (block, event_name))

    def check_nothing(self, event_name):
        self._trace_config.append('check_nothing(%s);' % event_name)

    def trace_comment(self, comment_str):
        self._trace_config.append('// %s;' % comment_str)

    def compose_test(self):
        self._trace_config = [
                '//Trace start',
                '//Generated by nvdla_base_test',
                '//You shall override compose_test',
                '//in your test',
                '//Trace end',
                ]

     # Generate trace dir
    def generate_trace(self):
        # Generate directory
        origin_working_directory = os.getcwd()
        os.chdir(self._generated_trace_dir)
        if not os.path.exists(self._name):
            os.mkdir(self._name)
        os.chdir(self._name)
        # Dump configuration to file
        with open(self._name+'.cfg', 'w') as f:
            f.write('\n'.join(self._trace_config))
        os.chdir(origin_working_directory)
        print ("Test generation done.")

if __name__ == '__main__':
    test = NvdlaBaseTest ('nv_small', '.')
    test.compose_test()
    test.generate_trace()
