import os
from csv import reader


class Node:
    def __init__(self, label, name, level, parent=None):
        # structural attributes
        self.label = label
        self.name = name
        self.children = []
        self.child_idx = []
        self.level = level
        self.parent = parent
        self.num_items = 0
        self.items = []  # (title, pub year, summary)

    def __str__(self, level=0):
        out = "\t"*level+repr(self.level)+": "+self.label+" - "\
             + self.name+"\n"
        for child in self.children:
            out += child.__str__(level+1)
        return out

    def print_nums(self, level=0):
        out = "\t"*level+repr(self.level)+": "+repr(self.label)+" - " \
            + repr(self.name) + " " + repr(self.num_items)+"\n"
        for child in self.children:
            out += child.print_nums(level+1)
        return out

    def add_child(self, node):
        self.children.append(node)
        self.child_idx.append(node.label)


class AlphaNode(Node):
    pass


class NumNode(Node):
    def __init__(self, label, name, level, parent=None):
        super().__init__(label, name, level, parent=None)
        self.min_val, self.max_val = self.get_min_max()

    def get_min_max(self):
        idx = self.get_first_digit()
        num_str = self.label[idx:].replace('(', '')\
            .replace(')', '').replace(self.label[0], '')
        # note: might want to add some additional functionality to handle
        #  cutter info
        if '.' in num_str:
            full_stop = num_str.index('.')
            if num_str[full_stop+1].isalpha():
                num_str = num_str[:full_stop]
        if '-' in num_str:
            min_max = num_str.split('-')
            min_val = float(min_max[0])
            max_val = float(min_max[1])
        else:
            min_val = float(num_str)
            max_val = float(num_str)
        return min_val, max_val

    def get_first_digit(self):
        i = 0
        for char in self.label:
            if char.isdigit():
                return i
            i += 1
        return -1


class LibraryTree:
    def __init__(self):
        self.classes = {}
        self.labels = ''
        self.hash_table = {}
        self.total_items = 0

    @staticmethod
    def read_csv(folder):
        data = []
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                f = subdir + os.sep + file
                cat = file[0]
                name = file[4:-4]
                with open(f, 'r', encoding="utf8") as read_obj:
                    csv_reader = reader(read_obj)
                    data.append((cat, name, list(csv_reader)))
        return data

    @staticmethod
    def parse_text(string, cat):
        space = string.index(" ")
        cat_idx = string.index(cat)
        label = string[cat_idx:space]
        name = string[space+1:].replace('\n', '')
        return label, name

    @staticmethod
    def get_cat_position(row):
        idx = [i for i in range(len(row)) if row[i] != '']
        if len(idx) > 1:
            print("ERROR")
        elif len(idx) == 0:
            return -1
        return idx[0]

    @staticmethod
    def find_lowest_cat(nodes, num):
        node = None
        valRang = 9999
        if num is not None:
            for label in nodes.keys():
                if label != 'node':
                    diff = label[1] - label[0]
                    if num >= label[0] and num <= label[1] and diff <= valRang:
                        node = nodes[label]
                        valRange = diff
        return node

    def csv_to_tree(self, csv_data):
        cat = csv_data[0]
        name = csv_data[1]
        csv = csv_data[2]
        root = AlphaNode(cat, name, 0)
        parent = root
        for row in csv:
            idx = self.get_cat_position(row)
            level = idx + 1
            if idx != -1:
                label, name = self.parse_text(row[idx], cat)
                if label.isalpha():
                    node = AlphaNode(label, name, level)
                else:
                    node = NumNode(label, name, level)
                if idx == parent.level:
                    node.parent = parent
                    parent.add_child(node)
                    parent = node
                else:
                    while idx != parent.level:
                        parent = parent.parent
                    node.parent = parent
                    parent.add_child(node)
                    parent = node
        return root

    def build_tree(self, folder):
        data = self.read_csv(folder)
        for csv in data:
            tree = self.csv_to_tree(csv)
            label = tree.label
            self.classes[label] = tree
            self.labels += tree.label

    def num_hash(self, node, hash_table):
        for child in node.children:
            hash_table[(child.min_val, child.max_val)] = child
            self.num_hash(child, hash_table)

    def alpha_hash(self, tree):
        if tree.label == 'E' or tree.label == 'F':
            sub_hash = {}
            self.num_hash(tree, sub_hash)
            sub_hash['node'] = tree
            self.hash_table[tree.label] = sub_hash
        else:
            self.hash_table[tree.label] = {'node': tree}
            for child in tree.children:
                sub_hash = {}
                self.num_hash(child, sub_hash)
                sub_hash['node'] = child
                self.hash_table[tree.label][child.label] = sub_hash

    def build_hash(self):
        for tree in self.classes.values():
            self.alpha_hash(tree)

    # OCLC number, LCCN, year published, title
    def add_item(self, node, item, label, subcat):
        if node is None:
            tree = self.hash_table[label]['node']
            if subcat in tree.child_idx:
                idx = tree.child_idx.index(subcat)
                tree.children[idx].num_items += 1
                tree.num_items += 1
                tree.items.append((item[3], item[2], item[4]))
                tree.children[idx].items.append(label)
                self.total_items += 1
        else:
            while node is not None:
                node.num_items += 1
                node.items.append((item[3], item[2],  item[4]))
                node = node.parent
            self.total_items += 1

    def count_items(self, item_list):
        for item in item_list:
            lcc = item[1]
            if lcc[0] == 'E' or lcc[0] == 'F':
                # F should not have a subcategory
                if lcc[1] is not None or lcc[2] is None:
                    continue
                nodes = self.hash_table[lcc[0]]
            elif lcc[0] in self.labels:
                if lcc[1] is None:
                    subcat = lcc[0]
                else:
                    subcat = lcc[0] + lcc[1]
                # ensure subcategory is valid
                try:
                    nodes = self.hash_table[lcc[0]][subcat]
                except KeyError:
                    continue
                node = self.find_lowest_cat(nodes, lcc[2])
                self.add_item(node, item, lcc[0], subcat)
            else:
                continue
