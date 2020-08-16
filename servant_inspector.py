import requests
import json
import pprint
import re
from bs4 import BeautifulSoup

STAR_SYMBOL_HTML = '&#11088;'
STAR_SYMBOL = '\u2606'
RIGHT_ARROW_SYMBOL = '\u2192'


def create_servant_list():
    r = requests.get('https://gamepress.gg/grandorder/servants')
    soup = BeautifulSoup(r.text, 'html.parser')

    servant_rows = soup.find_all(class_="servants-new-row")
    servant_list = []
    for servant_row in servant_rows:
        name_ref = servant_row.a['href']
        servant_list.append((servant_row.td.string.zfill(3), name_ref.split('/')[-1]))

    servant_list.sort()
    try:
        f = open('servants.txt', 'w')
        pp = pprint.PrettyPrinter(stream=f)
        pp.pprint([' '.join(x) for x in servant_list])
    finally:
        f.close()


def lookup_servant(serv_url: str):
    r = requests.get('https://gamepress.gg/grandorder/servant/' + serv_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    servantName = soup.find('h1').string
    servantClass = soup.find(class_="class-title").string
    # This shit's awful but they don't give us a nice version of rarity in the table, it's just a set of distinct star
    # image embeds. This extracts a number that we can cheat with
    servantRarity = soup.find(class_="class-rarity").div['about'].split('/')[-1]
    servantRarity = int(servantRarity) * STAR_SYMBOL

    # Some more awful shit I think because the spaces in between tags is being counted?
    non_whitespace = re.compile('\S+')
    traitslist = soup.find(class_="traits-list-servant")
    traits = ', '.join([trait.string for trait in traitslist if non_whitespace.match(trait.string)])

    all_skills = soup.findAll(class_="servant-skill")
    skilllist = []
    for skill in all_skills:
        # This cheats and takes advantage of expecting gg to order skill upgrades in order. If they don't then oops
        most_recent = skill.findAll(class_="servant-skill-right")[-1]
        # Stripped strings is all the words minus whitespace so I don't have to navigate the billion tags
        # they make per skill
        skilllist.append('\n'.join(most_recent.stripped_strings))

    no_upgrade = re.compile('\(Upgrade \d\)')
    np_tags = soup.find(class_="np-base-container").findAll(class_="servant-skill-right")[-1]
    # Everything about the NPs is awful. This is to get the title and then the desc is from <p> tags
    noblephantasm = no_upgrade.sub('', '\n'.join(np_tags.stripped_strings))

    # np_text_tags = np_tags.find_all('p')
    # for text in np_text_tags:
    #     print(text)

    if "Altria" in servantName:
        servantName = servantName.replace("Altria", "Artoria")

    print(servantName, servantClass, servantRarity)
    print(traits)
    print(skilllist)
    print(noblephantasm)


def lookup_asc_mats(serv_url: str):
    """"
    Gamepress baked color backgrounds in to the item images they host.
    Non transparency makes us sad so this is the backup if other stuff doesn't work.
    """
    r = requests.get('https://gamepress.gg/grandorder/servant/' + serv_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    mats_rows = soup.find_all(class_="ascension-row")

    for stage, row in enumerate(mats_rows, start=1):
        print(f"Ascension {stage}:")
        # Gamepress doesn't include a qp image so we have to do this extra step. The ascension-cost class helps though
        print(row.find(class_="ascension-cost").div.string, ":qp:")
        # Each material gets its own div with this class, we can drill down from there for the quantity and expected
        # emoji name
        for mat in row.find_all(class_="paragraph--type--required-materials"):
            quantity = mat['data-qty']
            emoji = mat.find('article')['about'].split('/')[-1]
            print(f"{quantity} :{emoji}:")


def atlas_lookup_asc_mats(atlas_serv_id: str):
    """"
    This looks up ascension mats from the Atlas API. Important to note that they
    have their own internal ids you're required to search by. The usual collection
    id is not supported by their endpoints, although they DO return it in the payload.
    """
    r = requests.get(f'https://api.atlasacademy.io/nice/JP/svt/{atlas_serv_id}?lang=en')
    data = r.json()
    all_mats = data['ascensionMaterials']
    # sample_data/atlas_asc_struct has an example of what we get back
    for stage, mats in all_mats.items():
        # Atlas API lists a stage 5 which is grailing. Idk if that's desired but I'm cutting it out for now
        if stage != "5":
            print('Ascension ' + stage)

            print_item_and_cost(mats)


def atlas_lookup_skill_mats(atlas_serv_id: str):
    """"
    This looks up skill mats from the Atlas API. Important to note that they
    have their own internal ids you're required to search by. The usual collection
    id is not supported by their endpoints, although they DO return it in the payload.
    """
    r = requests.get(f'https://api.atlasacademy.io/nice/JP/svt/{atlas_serv_id}?lang=en')
    data = r.json()
    all_mats = data['skillMaterials']
    for level, mats in all_mats.items():
        print(f'Level {level} {RIGHT_ARROW_SYMBOL} {int(level)+1}')

        print_item_and_cost(mats)

def print_item_and_cost(mats: json):
    """"
    Sure hope Atlas API doesn't change the structure of mats arrays.
    Would be an awful shame.
    Also I tried to give a type hint and had json like that was a real thing so I'm preserving that
    """
    cost = mats['qp']
    print(f'{cost} :qp:')

    for mat in mats['items']:
        mat_id = mat['item']['id']
        quantity = mat['amount']
        print(f"{quantity} :{mat_id}:")

if __name__ == "__main__":
    atlas_lookup_skill_mats('304000')