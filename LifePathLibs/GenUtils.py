import re


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