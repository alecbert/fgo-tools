import requests
import pprint
import re
from bs4 import BeautifulSoup

STAR_SYMBOL_HTML = '&#11088;'
STAR_SYMBOL = '\u2606'


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
    print(np_tags)
    # Everything about the NPs is awful. This is to get the title and then the desc is from <p> tags
    title_tag = np_tags.find_all('a')[0]
    # TODO FIX HAVING DOUBLE SPACES WHEN AN UPGRADE NOTE IS TAKEN AWAY
    noblephantasm = no_upgrade.sub('', ' '.join(title_tag.stripped_strings))
    print("shit \n\n")
    np_text_tags = np_tags.find_all('p')
    for text in np_text_tags:
        print(text)

    if "Altria" in servantName:
        servantName = servantName.replace("Altria", "Artoria")

    print(servantName, servantClass, servantRarity)
    print(traits)
    print(skilllist)
    print(noblephantasm)

if __name__ == "__main__":
    lookup_servant('voyager')