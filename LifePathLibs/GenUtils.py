import re
import pickle
import os.path
from collections import defaultdict, Mapping


class LifePathTables:
    def __init__(self):
        # 13d20 in total including finishing touches
        # Step 1: Homeland
        self.homelands = MinValDict()  # 2d20
        self.homelands_talents = FlatNameDict()
        # Step 2: Attributes
        self.attributes = MinValDict()  # 1d20
        # Step 3: Caste
        self.castes = MinValDict()  # 1d20
        self.castes_descriptions = FlatNameDict()
        self.castes_talents = FlatNameDict()
        # Step 4: Caste Story
        self.caste_stories = FlatNameDict()  # Contains nested MinValDict with stories per cast - 1d20
        self.caste_stories_descriptions = FlatNameDict()  # Nested CaseSpace dict with descs per cast
        # Step 5: Archetype
        self.archetypes = MinValDict()  # 1d20
        self.archetypes_descriptions = FlatNameDict()  # Contains descriptions and nested dict of values
        # Step 6: Nature
        self.natures = MinValDict()  # 1d20
        self.natures_descriptions = FlatNameDict()  # Contains descriptions and nested dict of values
        # Step 7: Education
        self.educations = MinValDict()  # 1d20
        self.educations_descriptions = FlatNameDict()
        # Step 8: War Story
        self.war_stories = MinValDict()  # 1d20
        # Step 9: Finishing Touches
        self.belongings = MinValDict()  # 1d20
        self.garments = MinValDict()  # 1d20
        self.weapons = MinValDict()  # 1d20
        self.provenance = MinValDict()  # 1d20

        self.talents = import_talents()

    def read_raw_table_dict(self, table_dict):
        for att_name, value in table_dict.items():
            getattr(self, att_name).update(value)
            for k, v in getattr(self, att_name).items():
                if isinstance(v, dict):
                    k2, v2 = next(iter(v.items()))
                    try:
                        int(k2)
                        new_val = MinValDict()
                        new_val.update(v)
                        getattr(self, att_name)[k] = new_val
                    except ValueError:
                        new_val = FlatNameDict()
                        new_val.update(v)
                        getattr(self, att_name)[k] = new_val


class FlatNameDict(dict):
    clean = re.compile('[^a-z]')

    def __init__(self, src_dict: dict=None):
        super(FlatNameDict, self).__init__()
        self.update(src_dict)

    def __getitem__(self, k: str):
        return super(FlatNameDict, self).__getitem__(re.sub(self.clean, '', k.lower()))

    @staticmethod
    def rand_val():
        return False

    def get(self, k: str):
        return super(FlatNameDict, self).get(re.sub(self.clean, '', k.lower()))

    def __setitem__(self, key: str, value):
        if isinstance(value, str):
            value = value.strip()
        super(FlatNameDict, self).__setitem__(re.sub(self.clean, '', key.lower()), value)

    def update(self, other=None, **kwargs):
        if other:
            for k, v in other.items() if isinstance(other, Mapping) else other:
                self[k] = v
            for k, v in kwargs.items():
                self[k] = v


class MinValDict(dict):
    def __getitem__(self, item):
        out = self.get(item)
        if not out:
            raise ValueError
        return out

    @staticmethod
    def rand_val():
        return True

    def get(self, k):
        if not isinstance(k, int):
            k = int(k)
        out = None
        while not out and k <= max(self.keys()):
            out = super(MinValDict, self).get(k)
            k += 1
        return out

    def __setitem__(self, key, value):
        if not isinstance(key, int):
            key = int(key)
        if isinstance(value, str):
            value = value.strip()
        super(MinValDict, self).__setitem__(key, value)


class Talent:
    def __init__(self, name, definition: tuple):
        self.name = name
        self.tier = 1
        self.attribute, self.skill, self.pre_requisites, self.max_ranks, self.description = \
            self.parse_definition(definition)

    def __str__(self):
        return self.name

    def set_tier(self, tier: int):
        self.tier = tier

    def matches_skills(self, skill_list):
        return self.skill.lower() in [s.lower() for s in skill_list]

    def cost(self, skills):
        sk_foc = skills.get(self.skill)['foc']
        return int((self.tier * 200) - (sk_foc * 25))

    def is_allowed(self, talents, skills):
        if not self.pre_requisites:
            return True
        char_talents = FlatNameDict(talents) if talents else {}
        char_skills = FlatNameDict(skills) if skills else {}
        if char_talents.get(self.name):
            return False  # Character already has this talent
        for req_talent in self.pre_requisites['talents']:
            if not char_talents.get(req_talent):
                return False  # Character lacks a required pre-requisite talent
        for skill_name, skill_req in self.pre_requisites['skills'].items():
            char_skill_dict = char_skills.get(skill_name)
            if not char_skill_dict:
                return False
            if not (char_skill_dict.get('exp', 0) >= skill_req.get('exp', 0) and
                    char_skill_dict.get('foc', 0) >= skill_req.get('foc', 0)):
                return False
        return True

    def parse_definition(self, definition):
        attribute, skill, temp_pre_requisites, max_ranks, description = definition
        return attribute, skill, self.convert_pre_requisites(temp_pre_requisites), max_ranks, description

    @staticmethod
    def convert_pre_requisites(temp_pre_requisites):
        foc, exp, talents, skills = 'foc', 'exp', 'talents', 'skills'
        skill_requirements = defaultdict(dict)
        talent_requirements = []
        for pre_req in temp_pre_requisites:
            if ' focus ' in pre_req.lower():  # focus pre-requisites
                skill, val = pre_req.lower().split(' focus ')
                skill_requirements[skill][foc] = int(val)
            elif ' expertise ' in pre_req.lower():  # expertise pre-requisites
                skill, val = pre_req.lower().split(' expertise ')
                skill_requirements[skill][exp] = int(val)
            elif ' or ' in pre_req:  # handling for or cases
                for talent in pre_req.split(' or '):
                    talent_requirements.append(talent)
                pass
            else:  # handling for talent requirements
                talent_requirements.append(pre_req)
                pass
        pre_requisites = {talents: talent_requirements, skills: {k: v for k, v in skill_requirements.items()}}
        if pre_requisites:
            print(pre_requisites)
        return pre_requisites


def import_talents() -> FlatNameDict:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    talent_file = os.path.join(script_dir, 'talent_tree.dat')
    with open(talent_file, 'rb') as talent_store_in:
        # return FlatNameDict(pickle.load(talent_store_in))
        return pickle.load(talent_store_in)
