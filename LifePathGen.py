import pickle
import os.path
import urllib.request
import random
from collections import defaultdict
import argparse
from LifePathLibs import CharacterSheet, Talent
from LifePathLibs import LifePathTables, MinValDict

# Needs 3 formatted int values: number to generate, min value, max value. 13, 1, 20 for 13d20
rand_api_path = "https://www.random.org/integers/?num=%d&min=%d&max=%d&col=1&base=10&format=plain&rnd=new"
attribute_names = ['Agility', 'Awareness', 'Brawn', 'Coordination', 'Intelligence', 'Personality', 'Willpower']


class CharacterMaker:
    def __init__(self, table_store: LifePathTables, true_random=False, full_auto=False, verbose=False, xp:int=0):
        self.table_store = table_store
        self.true_random = true_random
        self.full_auto = full_auto
        self.verbose = verbose
        self.xp = xp

        self.homeland = ''
        self.caste = ''
        self.caste_description = ''

        self.caste_story = ''
        self.caste_story_description = ''

        self.archetype = ''
        self.archetype_description = ''

        self.nature = ''
        self.nature_description = ''

        self.education = ''
        self.education_description = ''

        self.war_story = ''

        self.trait = ''
        self.attribute_aspects = []

        self.career_skill = ''
        self.ex_random_skill = ''
        self.finishing_touches =''
        self.talents = {}
        self.equipment = []
        self.attributes = {att: 7 for att in attribute_names}
        self.skills = defaultdict(lambda: {'exp': 0, 'foc': 0})
        self.languages = []
        self.standing = 0

        self.name = ''
        self.vigor = 0
        self.resolve = 0
        self.gold = 0
        self.gender = ''
        self.height = ''
        self.bonus_melee = 0
        self.bonus_ranged = 0
        self.bonus_presence = 0
        self.age = 0

        self.__generate_steps_rand()

    def calc_bonus_damage(self):
        d_vals = MinValDict()
        d_vals.update({8: 0, 9: 1, 11: 2, 13: 3, 15: 5, 25: 6})
        self.bonus_melee = d_vals[self.attributes['Brawn']]
        self.bonus_ranged = d_vals[self.attributes['Awareness']]
        self.bonus_presence = d_vals[self.attributes['Personality']]

    @staticmethod
    def rand_foot(rand_val: int):
        if rand_val < 2:
            return 4
        elif rand_val < 13:
            return 5
        elif rand_val < 20:
            return 6
        else:
            return 7

    def select_print(self, msg):
        if not self.full_auto:
            print(msg)

    def auto_print(self, msg):
        if self.verbose:
            print(msg)

    @staticmethod
    def un_camel(text):
        return text[0].lower() + text[1:] if text else ''

    @staticmethod
    def articelize(text):
        if not text:
            return ''
        return "an %s" % text if text[0].lower() in ('a', 'e', 'i', 'o', 'u') else "a %s" % text

    def skill_cost(self, skill):
        return {'exp': (200 * (skill['exp'] + 1)), 'foc': (200 * (skill['foc'] + 1))}

    def att_cost(self, attribute_level):
        return 100 * (attribute_level + 1)

    def allowed_talents(self):
        return list(filter(lambda t: t.is_allowed(self.talents, self.skills), self.table_store.talents.values()))

    def affordable_purchases(self):
        affordable_talents = {t: t.cost(self.skills) for t in self.allowed_talents() if t.cost(self.skills) <= self.xp}
        next_skill_costs = {n: self.skill_cost(s) for (n, s) in self.skills.items()}
        affordable_skill_exps = {n: v['exp'] for (n, v) in next_skill_costs.items() if v['exp'] <= self.xp}
        affordable_skill_focs = {n: v['foc'] for (n, v) in next_skill_costs.items() if v['foc'] <= self.xp}
        affordable_attributes = {n: self.att_cost(v) for (n, v) in self.attributes.items() if self.att_cost(v) <= self.xp}
        all_affordable = {}
        if affordable_talents:
            all_affordable['talents'] = affordable_talents
        if affordable_skill_exps:
            all_affordable['skill_exp'] = affordable_skill_exps
        if affordable_skill_focs:
            all_affordable['skill_foc'] = affordable_skill_focs
        if affordable_attributes:
            all_affordable['attributes'] = affordable_attributes
        return all_affordable

    def select_from_choices(self, prompt, choices: list):
        if not isinstance(choices, list):
            choices = list(choices)
        if self.full_auto:
            auto_choice = choices[arbitrary_random(0, len(choices)-1)]
            self.auto_print("Automatically selecting %s from choices: %s" % (auto_choice, ', '.join(choices)))
            return auto_choice
        else:
            nums = [str(n + 1) for n in range(len(choices))]
            vals = {n: choice for n, choice in zip(nums, choices)}
            select_vals = sorted(['[%s]: %s' % (n, choice) for n, choice in vals.items()])
            input_prompt = '%s\n%s\nYour choice: ' % (prompt, '\n'.join(select_vals))
            selected = input(input_prompt)
            while selected not in choices + nums:
                print('Selected value: "%s" not valid, choose a value from the following:\n%s.' %
                      (selected, ', '.join(choices)))
                selected = input(input_prompt)
            return selected if selected in choices else vals[selected]

    def __generate_steps_rand(self):
        rand_vals = roll_dice('14d20', true_random=self.true_random)

        self.step1_homeland(rand_vals.pop() + rand_vals.pop())
        self.step2_attributes((rand_vals.pop(), rand_vals.pop()))
        self.step3_caste(rand_vals.pop())
        self.step4_story(rand_vals.pop())
        self.step5_archetype(rand_vals.pop())
        self.step6_nature(rand_vals.pop())
        self.step7_education(rand_vals.pop())
        self.step8_war_story(rand_vals.pop())
        self.step9_finishing_touches(rand_vals)
        self.step10_calcs_and_naming()
        self.step11_randomize_xp()

    def add_skill(self, skill: str, exp: int, foc: int):
        if 'character’s career skill' in skill:
            self.auto_print("Boosting career skill %s" % self.career_skill)
            self.skills[self.career_skill]['exp'] += exp
            self.skills[self.career_skill]['foc'] += foc
        elif "random career skill" in skill:
            self.auto_print("Adding random career skill from education")
            self.add_random_career_skill(roll_dice('1d20', self.true_random))
        else:
            self.skills[skill]['exp'] += exp
            self.skills[skill]['foc'] += foc

    def clean_step(self, step_info):
        if isinstance(step_info, str):
            return step_info.strip()
        else:
            return tuple(val.strip() for val in step_info)

    @staticmethod
    def split_and_clean_list(list_txt: str, list_sep: str) -> list:
        return list_txt.split(list_sep)[1]\
            .replace(', or ', ', ').replace(', and ', ', ').replace(', page 23', '').split(', ')

    def parse_skills_talents_equip(self, values: dict, skill_type: str):
        talent_src_skills = []
        if 'careertalent' in values:
            talent, page = values['careertalent'].split('(')
            self.talents[talent.strip()] = page.strip().replace(')', '')
        if 'careerskill' in values:
            self.career_skill = values['careerskill'].split('in the ')[1].replace(' skill', '')
            self.add_skill(self.career_skill, 2, 2)  # Career skill is +2/+2
        if 'mandatoryskills' in values:
            mandatory_skills = self.split_and_clean_list(values['mandatoryskills'], ' to ')
            talent_src_skills += mandatory_skills
            for skill in mandatory_skills:
                self.add_skill(skill, 1, 1)  # Mandatory skills are +1/+1 for both archetype and nature
        if 'electiveskills' in values:
            elective_skills = self.split_and_clean_list(values['electiveskills'], 'following skills: ')
            talent_src_skills += elective_skills
            self.select_print(
                "Select 2 elective skills to each get +1EXP/+1FOC. %s grants you the following elective skills:\n%s" %
                (skill_type, ', '.join(elective_skills)))
            for order in ('first', 'second'):
                skill_elect = self.select_from_choices("Select the %s skill to get +1EXP/+1FOC:\n" % order, elective_skills)
                self.add_skill(skill_elect, 1, 1)
                elective_skills.remove(skill_elect)
        if 'talent' in values:
            skill_choices = [s.replace("your character’s career skill", self.career_skill)
                             .replace("a random career skill (roll on Archetype table)", self.ex_random_skill)
                             for s in talent_src_skills]
            talent_choices = {v.name: v for (k, v) in self.table_store.talents.items() if v.is_allowed(self.talents, self.skills)
                              and v.matches_skills(skill_choices)}
            talent_names = list(set(talent_choices.keys()))
            selected_talent = self.select_from_choices(
                "Choose any one talent associated with one of the following skills:\n%s" %
                ', '.join(talent_names), talent_names)
            self.talents[selected_talent] = talent_choices[selected_talent].description
        if 'equipment' in values:
            self.equipment += values['equipment'].split('\n')
        if 'attributeimprovement' in values:
            self.attributes[values['attributeimprovement'].split(' to ')[1]] += 1

    def add_random_career_skill(self, rand_val):
        archetype = self.clean_step(self.table_store.archetypes.get(rand_val))
        archetype_description, arch_vals = self.table_store.archetypes_descriptions.get(archetype)
        ex_random_skill = arch_vals['careerskill']
        self.ex_random_skill = ex_random_skill.split('in the ')[1].replace(' skill', '')
        self.parse_skills_talents_equip({'careerskill': ex_random_skill},
                                        "Your additional random (%s) archetype" % archetype)

    def step1_homeland(self, rand_val):
        # Homeland, Talent, Languages
        homeland_info = self.clean_step(self.table_store.homelands.get(rand_val))
        self.homeland = homeland_info[0]
        self.talents[homeland_info[1]] = self.table_store.homelands_talents.get(homeland_info[1])
        self.languages.append(homeland_info[2])

    def step2_attributes(self, rand_vals):
        optionals = []
        aspects = set()
        mandatories = []
        for val in rand_vals:
            aspect, mandatory1, mandatory2, optional1, optional2 = self.clean_step(self.table_store.attributes.get(val))
            optionals.append((aspect, optional1, optional2))
            aspects.add(aspect)
            mandatories.append(mandatory1)
            mandatories.append(mandatory2)
        for aspect in aspects:
            self.attribute_aspects.append(aspect)

        same = len(aspects) == 1
        if not same:
            aspect_txt = "your character is both %s" % ' and '.join(aspects)
            self.select_print('Because %s, your mandatory attributes are:\n%s' % (aspect_txt, ', '.join(mandatories)))
        best = self.select_from_choices('Select your "best" mandatory attribute (+3 to attribute):\n', mandatories)
        mandatories.remove(best)
        worst = self.select_from_choices('Select your "worst" mandatory attribute (+1 to attribute):\n', mandatories)
        while worst == best:
            self.select_print("You cannot select the same trait as best and worst")
            worst = self.select_from_choices('Select your "worst" mandatory attribute (+1 to attribute):\n', mandatories)
        mandatories.remove(worst)
        if same:
            help_txt = "Because your character only has one aspect, both attributes get +2 as well"
        else:
            help_txt = "Your character's other mandatory attributes also get +2 each"
        self.attributes[best] += 3
        self.attributes[worst] += 1
        for other in mandatories:
            self.attributes[other] += 2
        for aspect, optional1, optional2 in optionals:
            choice = self.select_from_choices("Select either %s or %s to get another +1:\n" % (optional1, optional2),
                                              (optional1, optional2))
            self.attributes[choice] += 1

    def step3_caste(self, rand_val):
        # caste, talents, skill, standing
        caste_info = self.clean_step(self.table_store.castes.get(rand_val))
        self.caste = caste_info[0]
        self.caste_description = self.table_store.castes_descriptions.get(self.caste)
        for talent in caste_info[1].split(','):
            self.talents[talent] = self.table_store.castes_talents.get(talent)
        self.add_skill(caste_info[2], 1, 1)
        self.standing += int(caste_info[3])

    def step4_story(self, rand_val):
        # Name, trait
        story_info = self.clean_step(self.table_store.caste_stories.get(self.caste).get(rand_val))
        self.caste_story = story_info[0]
        self.caste_story_description = self.table_store.caste_stories_descriptions.get(self.caste).get(self.caste_story)
        self.trait = story_info[1]

    def step5_archetype(self, rand_val):
        self.archetype = self.clean_step(self.table_store.archetypes.get(rand_val))
        self.archetype_description, arch_vals = self.table_store.archetypes_descriptions.get(self.archetype)
        self.parse_skills_talents_equip(arch_vals, "Your %s archetype" % self.un_camel(self.archetype))

    def step6_nature(self, rand_val):
        self.nature = self.table_store.natures.get(rand_val)
        self.nature_description, nature_vals = self.table_store.natures_descriptions.get(self.nature)
        self.parse_skills_talents_equip(nature_vals, "Your %s nature" % self.un_camel(self.nature))

    def step7_education(self, rand_val):
        self.education = self.table_store.educations[rand_val]
        self.education_description, ed_vals = self.table_store.educations_descriptions[self.education]
        self.parse_skills_talents_equip(ed_vals, "Your %s education" % self.un_camel(self.education))

    def step8_war_story(self, rand_val):
        war_story, war_bonus = self.table_store.war_stories[rand_val]
        self.war_story = war_story.strip().lower()
        if self.war_story.count(" ") == 0:
            self.war_story = "were %s" % self.war_story
        war_skills = war_bonus.split(' to ')[1].split(' and ')
        list(map(lambda ws: self.add_skill(ws, 1, 1), war_skills))

    def step9_finishing_touches(self, rand_vals):
        self.equipment.append(self.table_store.garments[rand_vals.pop()])
        self.equipment.append(self.table_store.belongings[rand_vals.pop()])
        weapon = self.table_store.weapons[rand_vals.pop()]
        provenance = self.table_store.provenance[rand_vals.pop()]
        prov_weap = provenance.replace('...', " %s " % weapon).replace('…', " %s " % weapon).replace(' , ', ', ')
        if prov_weap.startswith(' '):
            prov_weap = self.articelize(prov_weap[1:])
        self.equipment.append("Weapon: %s (see Chapter 4 of player guide for stats)" % prov_weap)
        self.finishing_touches = \
            "Now that your character is generated, remember to complete your finishing touches.\n" \
            "Skills:\n" \
            "\tDistribute 3 exp/foc among your skills however you desire.\n" \
            "Talent:\n" \
            "\tChoose one additional talent provided you meet the prerequisites " \
            "(Also check above for talent choices from character creation)\n" \
            "Language:\n" \
            "\t Pick an extra language, plus one additional extra language for each point of foc in Linguistics\n" \
            ""

    def step10_calcs_and_naming(self):
        self.vigor = self.attributes.get('Brawn') + self.skills.get('Resistance', {}).get('exp', 0)
        self.resolve = self.attributes.get('Willpower') + self.skills.get('Discipline', {}).get('exp', 0)
        self.gold = self.attributes.get('Personality') + self.skills.get('Society', {}).get('exp', 0)
        self.height = "%d'%d\"" % (self.rand_foot(arbitrary_random()), arbitrary_random(0, 11))
        self.gender = self.select_from_choices("Select your character's gender:", ["Male", "Female"])
        self.calc_bonus_damage()
        pronoun = "him" if self.gender == "Male" else "her"
        self.name = input("Enter a name for your character to save %s, or leave blank and character will be printed in "
                          "the terminal but not saved:" % pronoun)
        self.age = arbitrary_random(15, 40)

    def step11_randomize_xp(self):
        all_affordable = self.affordable_purchases()
        while all_affordable:
            upg_type = random.sample(list(all_affordable), 1)[0]
            upg_key = random.sample(all_affordable[upg_type].keys(), 1)[0]
            upg_cost = all_affordable[upg_type][upg_key]
            if upg_type == 'attributes':
                self.attributes[upg_key] += 1
                print("Spent %d xp to raise the value of the %s attribute by 1 point" % (upg_cost, upg_key))
            elif upg_type == 'talents':
                self.talents[upg_key.name] = upg_key
                print("Spent %d xp to purchase the talent %s" % (upg_cost, upg_key))
            elif 'exp' in upg_type:
                self.skills[upg_key]['exp'] += 1
                print("Spent %d xp to raise exp in the %s skill by 1 point" % (upg_cost, upg_key))
            elif 'foc' in upg_type:
                self.skills[upg_key]['foc'] += 1
                print("Spent %d xp to raise foc in the %s skill by 1 point" % (upg_cost, upg_key))
            self.xp -= upg_cost
            all_affordable = self.affordable_purchases()

    def __str__(self):
        char_str = "\nYou are %s from the land of %s.\n" % (self.articelize(self.un_camel(self.caste)), self.homeland) + \
            "You are generally considered to be %s.\n" % (', and '.join(self.attribute_aspects)) +\
            "Your past has been defined by %s. %s\nBut you also know that %s.\n" % \
                   (self.caste_story, self.caste_story_description, self.un_camel(self.nature_description)) +\
            'You describe your education as having been %s. %s.\n' % (self.education, self.education_description) +\
            "Your life has changed since you become %s. These days, %s.\n" % \
                   (self.articelize(self.archetype), self.un_camel(self.archetype_description)) +\
            "Recently, you find your life increasingly defined by %s and your %s nature.\n" \
                   % (self.un_camel(self.trait), self.un_camel(self.nature)) +\
            "But you will never forget your time at war, when you %s.\n" % self.war_story +\
            "------------------------------------------\n" +\
            "Your stats are as follows:\n" +\
            "Homeland:\n\t%s\n" % self.homeland +\
            "Languages Spoken:\n\t%s\n" % ','.join(self.languages) +\
            "Social Standing:\n\t%d\n" % self.standing +\
            "Attributes:\n\t%s\n" % '\n\t'.join(["%s - %s" % (k, v) for (k, v) in self.attributes.items()]) +\
            "Talents:\n\t%s\n" % '\n\t'.join(["%s: %s" % (k, v) for k, v in self.talents.items()]) +\
            "Skills:\n\t%s\n" % '\n\t'.join(['%s: %s' % (k, '%d EXP/%d FOC' % (v['exp'], v['foc']))
                                             for (k, v) in self.skills.items()]) +\
            "Equipment:\n\t%s\n" % '\n\t'.join(self.equipment) +\
            "\n--------------------------------\n%s" % self.finishing_touches
        # return ''
        return char_str


def roll_dice(roll_type: str, true_random=False):
    num_die, die_max = roll_type.split('d')
    return arbitrary_random(1, int(die_max), int(num_die), true_random)


def arbitrary_random(min_val=1, max_val=20, num_vals=1, true_random=False):
    if true_random:
        with urllib.request.urlopen(rand_api_path % (num_vals, min_val, max_val)) as randoms:
            nums = [int(n) for n in randoms.read().strip().split(b'\n')]
    else:
        nums = [random.randint(min_val, max_val) for i in range(num_vals)]
    r_val = nums[0] if num_vals == 1 else nums
    return r_val


def gen_character(true_random=False, full_auto=False, verbose=False, xp:int=0):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    table_file = os.path.join(script_dir, 'LifePathLibs', 'tables.dat')
    table_store = LifePathTables()
    with open(table_file, 'rb') as table_store_in:
        table_dict = pickle.load(table_store_in)
        table_store.read_raw_table_dict(table_dict)
    char_maker = CharacterMaker(table_store, true_random=true_random, full_auto=full_auto, verbose=verbose, xp=xp)
    return char_maker


def parse_args():
    parser = argparse.ArgumentParser(description="Conan character generator parsed from PDF with some hand-fiddling "
                                                 "to clean things up.")
    parser.add_argument('-f', "--full-auto", action='store_true', default=False,
                        help="Turns on full-auto mode. In this mode, the generator will automatically make all "
                             "selections randomly or psuedo-randomly with no user input.")
    parser.add_argument('-t', "--true-random", action='store_true', default=False,
                        help="Enables truly random usage (from random.org). This makes the code a bit slower since the "
                             "random numbers are coming over the web, but if you want true randomness, enable it. The"
                             "default is to use psuedo-random numbers from Python.")
    parser.add_argument('-v', "--verbose", action="store_true", default=False,
                        help="Turn on verbose printing. when using full-auto mode, this will log automatic choices.")
    parser.add_argument('-o', "--out-dir", type=str, default=os.path.dirname(os.path.realpath(__file__)),
                        help="Output directory to save importable XML with generated character information.")
    parser.add_argument('-x', "--xp", type=int, default=0,
                        help="Specify a value of XP to randomly spend on skill, talent and attribute upgrades "
                             "for your character")
    return parser.parse_args()


def main():
    args = parse_args()
    char = gen_character(args.true_random, args.full_auto, args.verbose, args.xp)
    if char.name:
        sheet = CharacterSheet(char)
        out_dir = args.out_dir
        f_name = "FG_import_" + char.name.replace(' ', '') + '.xml'
        save_file = os.path.join(out_dir, f_name)
        print(save_file)
        with open(save_file, 'w') as xml_out:
            xml_out.write(sheet.create_fg_xml())
    else:
        print(char)


if __name__ == '__main__':
    main()
