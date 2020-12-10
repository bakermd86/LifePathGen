from LifePathLibs import att_map, Attributes
from os.path import join, dirname, realpath

template_file = 'FG2MoreCoreTemplate.xmlt'
# Template numbers = 5 digit number, starting at 00001

ability_temp = '<id-%(ability_num)s><name type="string">%(ability_name)s</name>' \
               '<shortcut type="windowreference"><class>ability</class><recordname></recordname></shortcut>' \
               '<text type="formattedtext"><p>%(ability_text)s</p></text></id-%(ability_num)s>\n'

# For attributes, foc_mod is always 0. For skills, att_skill_val is the attribute value + the EXP
att_skill_temp = '<id-%(att_skill_num)s><clichatcommand type="string">/conan 2d20x%(att_skill_val)dy%(foc_mod)d' \
                 '</clichatcommand><description type="formattedtext"><p></p></description><name type="string">' \
                 '%(att_skill_name)s</name><rollstype type="string">conan</rollstype><shortcut type="windowreference">'\
                 '<class>cas</class><recordname></recordname></shortcut></id-%(att_skill_num)s>\n'
cli_list_wrapper = '<clilist%(att_map)s>%(att_skill_body)s</clilist%(att_map)s>\n'
cli_list_map = {'1': 'Agility', '1a': 'Coordination', '2': 'Awareness', '2a': 'Intelligence', '3': 'Brawn/Willpower',
                '3a': 'Personality'}

equip_temp = '<id-%(equip_num)s><carried type="number">1</carried><count type="number">1</count><isidentified ' \
             'type="number">1</isidentified><name type="string">%(item_name)s</name><weight type="number">?</weight>' \
             '</id-%(equip_num)s>\n'

language_temp = '<id-%(language_num)s><name type="string">%(language)s</name></id-%(language_num)s>\n'

attacks_temp = 'Unarmed: (Reach 1-Improvised-Stun-2D): %dd6,\\n' \
               'Throw Rock: (Reach 2-Improvised-Stun-Thrown-2D): %dd6,\\n' \
               'Intimidate: (Close-Mental-Stun-2D): %dd6,\\n'  # 2+bonus_melee, 2+ bonus_range, 2+ bonus_presence


class CharacterSheet:
    def __init__(self, char):
        self.script_dir = dirname(realpath(__file__))
        # Declare all variables to be interpolated into the XML
        self.name = char.name
        self.race = char.homeland
        self.talents = char.talents
        self.char_age = char.age
        self.char_summary = ''

        self.char_attributes = char.attributes  # dictionary of attributes
        self.char_skills = char.skills  # dictionary of skills.

        self.equipment = char.equipment
        self.languages = char.languages

        self.renown = 0
        self.standing = char.standing
        self.bonus_ranged = char.bonus_ranged
        self.bonus_melee = char.bonus_melee
        self.bonus_presence = char.bonus_presence
        self.attacks = self.format_attacks()

        self.vigor = char.vigor
        self.resolve = char.resolve
        self.gold = char.gold
        self.gender = char.gender
        self.height = char.height

        self.notes = str(char)

    def format_attacks(self):
        return attacks_temp % (2 + self.bonus_melee, 2 + self.bonus_ranged, 2 + self.bonus_presence)

    def read_template(self):
        with open(join(self.script_dir, template_file)) as fg_template:
            return fg_template.read()

    def create_fg_xml(self):
        body_template = self.read_template()
        formatter = self.create_template_formatter()
        return body_template % formatter

    def create_template_formatter(self):
        fmt_dict = {'char_age': self.char_age, 'char_summary': self.char_summary, 'renown': self.renown,
                    'name': self.name, 'standing': self.standing, 'bonus_ranged': self.bonus_ranged,
                    'bonus_melee': self.bonus_melee, 'bonus_presence': self.bonus_presence, 'vigor': self.vigor,
                    'resolve': self.resolve, 'race': self.race, 'notes': self.notes.replace('\n', '\\n'),
                    'gold': self.gold, 'gender': self.gender, 'height': self.height, 'attacks': self.attacks,
                    'abilities': self.parse_abilities(),
                    'attributes_and_skills': self.parse_attributes_and_skills(),
                    'equipment': self.parse_equipment(),
                    'languages': self.parse_langauges(),
                    }
        return fmt_dict

    def parse_langauges(self):
        languages = ''
        i = 1
        for language in self.languages:
            lang_fmt = {'language_num': '%05d' % i, 'language': language}
            languages += language_temp % lang_fmt
            i += 1
        return languages

    def parse_equipment(self):
        equipment = ''
        i = 1
        for item_name in self.equipment:
            equip_fmt = {'equip_num': '%05d' % i, 'item_name': item_name}
            equipment += equip_temp % equip_fmt
            i += 1
        return equipment

    def parse_abilities(self):
        abilities = ''
        i = 1
        # print(self.talents)
        for ability_name, ability_text in self.talents.items():
            # print(ability)
            ability_fmt = {
                'ability_num': '%05d' % i,
                "ability_name": ability_name,
                "ability_text": ability_text
            }
            # ability_fmt['ability_name'] = ability_name
            # ability_fmt['ability_text'] = ability_text
            abilities += ability_temp % ability_fmt
            i += 1
        return abilities

    def parse_attribute(self, attribute_name, att_num=1):
        attribute_val = self.char_attributes.get(attribute_name)
        if not attribute_val:
            return '', 0
        skills = [s.value for s in att_map.get(Attributes[attribute_name.lower()])]
        att_fmt = {'att_skill_name': '%s - %d' % (attribute_name, attribute_val), 'foc_mod': 0,
                   'att_skill_val': attribute_val, 'att_skill_num': '%05d' % att_num}
        att_body = att_skill_temp % att_fmt

        for skill in skills:
            att_num += 1
            exp = self.char_skills[skill]['exp']
            foc = self.char_skills[skill]['foc']
            skill_fmt = {'att_skill_num': '%05d' % att_num, 'foc_mod': foc, 'att_skill_val': attribute_val + exp}
            if exp or foc:
                skill_fmt['att_skill_name'] = '%s - %dEXP/%dFOC' % (skill, exp, foc)
            else:
                skill_fmt['att_skill_name'] = skill
            att_body += att_skill_temp % skill_fmt
        return att_body, att_num

    def parse_attributes_and_skills(self):
        attributes_and_skills = ''
        for cli_num, att_name in sorted(cli_list_map.items()):
            if att_name == 'Brawn/Willpower':
                att_body = ''
                att_num = 1
                for attribute_name in att_name.split('/'):
                    body_tmp, num_tmp = self.parse_attribute(attribute_name, att_num)
                    att_body += body_tmp
                    att_num += num_tmp
            else:
                att_body, att_num = self.parse_attribute(att_name)
            attributes_and_skills += cli_list_wrapper % {'att_map': cli_num, 'att_skill_body': att_body}
        return attributes_and_skills
