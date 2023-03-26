from mathutils import (Vector, Quaternion, Matrix, Euler)
from enum import Enum
import os

class ValueType(Enum):
    DEFAULT = 1
    INDICES = 2
    VERTICES = 3
    BONE = 4

class GTA_Parser:
    def __init__(self):
        self.name = ""
        self.path = ""
        self.folder = ""
        self.subfolder = ""
        self.data_lines = []
        self.data = []

    def getMemberByName(self, name):
        def findMember(parent, name):
            for key, value in parent.items():
                if key == name:
                    return value
            for member in parent["members"]:
                if member["name"] == name:
                    return member
                if member["members"]:
                    res_children = findMember(member, name)
                    if res_children:
                        return res_children
            return None
        return findMember(self.data, name)

    def read_file(self, filepath):
        def getVertices(line, member):
            raw_vertex = [sp.split() for sp in line.split(' / ')]
            # vector_list = [Vector(float(p) for p in v) for v in raw_vertex]
            vector_list = [Vector(map(float, v)) for v in raw_vertex]
            member["vertices"].append(vector_list)
            member["positions"].append(vector_list[0])

        def getFaces(line, member):
            raw_indeces = list(map(int, line.split()))
            member["faces"].extend(zip(*(iter(raw_indeces),) * 3))
            # member["faces"].extend([[raw_indeces[i*3], raw_indeces[i*3+1], raw_indeces[i*3+2]] for i in range(int(len(raw_indeces)/3))])

        def setMemberName(member, split):
            member["name"] = split[0]
            if len(split) > 1:
                member["attributes"] = split[1:]

        def getValueType(line):
            name = line[0]
            if name == "Indices":
                return ValueType.INDICES
            if name == "Vertices":
                return ValueType.VERTICES
            else:
                return ValueType.DEFAULT


        def get_data_blocks(start_line, v_type=ValueType.DEFAULT):
            this_member = {"name": "", "attributes": [], "members": [], "values": []}
            prev_line = []
            line_number = start_line

            if v_type == ValueType.INDICES:
                this_member["faces"] = []
            elif v_type == ValueType.VERTICES:
                this_member["positions"] = []
                this_member["vertices"] = []

            def addPrevLine(member, prev_line):
                if prev_line:
                    if len(prev_line) > 1:
                        member[prev_line[0]] = prev_line[1:] if len(prev_line[1:]) > 1 else prev_line[1]
                    else:
                        member["values"].append(prev_line[0])

            while line_number < len(self.data_lines):
                line = self.data_lines[line_number]
                if "{" in line:
                     # jump to line afer last block
                    child_member, line_number = get_data_blocks(line_number + 1, getValueType(prev_line))
                    setMemberName(child_member, prev_line)
                    this_member["members"].append(child_member)
                    # rest prev_line
                    prev_line = []
                    continue
                elif "}" not in line:
                    if v_type == ValueType.VERTICES:
                        getVertices(line, this_member)
                    elif v_type == ValueType.INDICES:
                        getFaces(line, this_member)
                    else:
                        addPrevLine(this_member, prev_line)
                        prev_line = line.split()
                elif "}" in line:
                    addPrevLine(this_member, prev_line)
                    return this_member, line_number + 1
                line_number += 1

            return this_member

        if filepath and os.path.exists(filepath):
            self.name = os.path.basename(filepath).split(".")[0]
            self.path = filepath
            self.folder = os.path.dirname(filepath)
            self.subfolder = os.path.join(self.folder, self.name)
            with open(filepath, 'r') as file:
                self.data_lines = file.read().splitlines()
            self.data = get_data_blocks(0)
            return True
        else:
            print("path does not exist: {0}".format(filepath))
            return False
