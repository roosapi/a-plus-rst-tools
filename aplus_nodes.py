from docutils import nodes
import os.path
import re
import yaml_writer


class html(nodes.General, nodes.Element):

    def __init__(self, tagname, attributes={}):
        self.tagname = tagname
        super().__init__(rawsource='', **attributes)

    def write_yaml(self, env, name, data_dict):
        self.yaml_data = data_dict
        self.yaml_write = yaml_writer.file_path(env, name)

    def set_yaml(self, data_dict):
        self.yaml_data = data_dict

    def pop_yaml(self):
        data = self.yaml_data
        del self.yaml_data
        return data


def recursive_collect(node):
    data = []
    for child in node.children:
        if hasattr(child, 'yaml_data'):
            data.append(child.pop_yaml())
        data.extend(recursive_collect(child))
    return data


def recursive_fill(data_dict, node, html):
    for key,val in data_dict.items():
        if isinstance(val, tuple):
            if val[0] == '#!children':
                data_dict[key] = recursive_collect(node)
            elif val[0] == '#!html':
                res = re.findall(val[1], html, re.DOTALL)
                data_dict[key] = res[0] if len(res) > 0 else ''
        elif isinstance(data_dict[key], dict):
            recursive_fill(data_dict[key], node, html)
        elif isinstance(data_dict[key], list):
            for a_dict in [a for a in data_dict[key] if isinstance(a, dict)]:
                recursive_fill(a_dict, node, html)


def visit_html(self, node):
    node._body_begin = len(self.body)
    self.body.append(node.starttag())


def depart_html(self, node):
    self.body.append(node.endtag())
    if hasattr(node, 'yaml_data'):
        recursive_fill(node.yaml_data, node, ''.join(self.body[node._body_begin:]))
        if hasattr(node, 'yaml_write'):
            yaml_writer.write(node.yaml_write, node.yaml_data)
