# coding: utf-8

import unittest

from OracleTest import OracleTest
from card.components import SetOracle
from core.utils import DummyLogger


class TestSetOracle(OracleTest):
    def get_oracle(self):
        return SetOracle(DummyLogger(), thorough=True)

    def test_core_sets(self):
        self.e('LEA', ['Limited Edition Alpha', 'Alpha', 'Alpha Edition', 'A'])
        self.e('LEB', ['Limited Edition Beta', 'Beta', 'Beta Edition'])
        self.e('2ED', ['Unlimited Edition', '2E', 'Unlimited'])
        self.e('RSM', ['Revised Edition (Summer Magic)'])
        self.e('3FB', ['Revised Edition (FBB)', '3rd Edition (FBB)'])
        self.e('3WB', ['Revised Edition (FWB)', '3rd Edition (FWB)'])
        self.e('3ED', ['Revised Edition', '3E', 'Revised'])
        self.e('4FB', ['Fourth Edition (FBB)', '4th Edition (FBB)', '4EF'])
        self.e('4WB', ['Fourth Edition (FWB)', '4th Edition (FWB)'])
        self.e('4ED', ['Fourth Edition', '4th Edition', '4E', 'Четвертая редакция', 'Четвёртая редакция', '4 редакция'])
        self.e('4EA', ['Alternate Fourth Edition', 'Alternate 4th Edition'])
        self.e('5ED', ['Fifth Edition', '5th Edition', '5E', 'Пятая редакция', '5 редакция'])
        self.e('6ED', ['Sixth Edition', '6th Edition', '6E', 'Classic Sixth Edition', 'Шестая редакция', '6 редакция'])
        self.e('7ED', ['Seventh Edition', '7th Edition', '7E', 'Седьмая редакция', '7 редакция'])
        self.e('8ED', ['Eighth Edition', '8th Edition', '8E', 'Eighth Edition Box Set', '8EB', 'Восьмая редакция', '8 редакция'])
        self.e('9ED', ['Ninth Edition', '9th Edition', '9E', 'Ninth Edition Box Set', '9EB', 'Девятая редакция', '9 редакция'])
        self.e('10E', ['Tenth Edition', '10th Edition', 'Десятая редакция', '10 редакция'])
        self.e('M10', ['Magic 2010', 'Magic 2010 (M10)', 'Magic 2010 Core Set', '2010 Core Set', 'Core Set 2010', 'Синглы M10', 'Синглы М10', 'Базовый Выпуск 2010'])
        self.e('M11', ['Magic 2011', 'Magic 2011 (M11)', 'Magic 2011 Core Set', '2011 Core Set', 'Core Set 2011', 'Синглы M11', 'Синглы М11', 'Базовый Выпуск 2011'])
        self.e('M12', ['Magic 2012', 'Magic 2012 (M12)', 'Magic 2012 Core Set', '2012 Core Set', 'Core Set 2012', 'Синглы M12', 'Синглы М12', 'Базовый Выпуск 2012'])
        self.e('M13', ['Magic 2013', 'Magic 2013 (M13)', 'Magic 2013 Core Set', '2013 Core Set', 'Core Set 2013', 'Синглы M13', 'Синглы М13', 'Базовый Выпуск 2013'])
        self.e('M14', ['Magic 2014', 'Magic 2014 (M14)', 'Magic 2014 Core Set', '2014 Core Set', 'Core Set 2014', 'Синглы M14', 'Синглы М14', 'Базовый Выпуск 2014'])
        self.e('M15', ['Magic 2015', 'Magic 2015 (M15)', 'Magic 2015 Core Set', '2015 Core Set', 'Core Set 2015', 'Синглы M15', 'Синглы М15', 'Базовый Выпуск 2015'])
        self.e('M19', ['Magic 2019', 'Magic 2019 (M19)', 'Magic 2019 Core Set', '2019 Core Set', 'Core Set 2019', 'Синглы M19', 'Синглы М19', 'Базовый Выпуск 2019'])
        self.e('ORI', ['Magic Origins', 'Origins', 'Magic: Истоки'])

    def test_expansion_sets(self):
        self.e('ARN', ['Arabian Nights', 'Арабские ночи'])
        self.e('ATQ', ['Antiquities'])
        self.e('LEG', ['Legends', 'Легенды'])
        self.e('DRK', ['The Dark', 'DK', 'Тьма'])
        self.e('FEM', ['Fallen Empires', 'FE', 'Павшие империи'])
        self.e('HML', ['Homelands', 'HL', 'Родные земли'])

        self.e('MIR', ['Mirage', 'Мираж'])
        self.e('VIS', ['Visions', 'VI', 'Видения'])
        self.e('WTH', ['Weatherlight', 'WL'])

        self.e('TMP', ['Tempest', 'TE', 'Буря'])
        self.e('STH', ['Stronghold', 'SH', 'Твердыня'])
        self.e('EXO', ['Exodus', 'EX', 'Исход'])

        self.e('USG', ["Urza's Saga", 'US', 'Сага Урзы'])
        self.e('ULG', ["Urza's Legacy", 'UL', 'Наследие Урзы'])
        self.e('UDS', ["Urza's Destiny", 'UD', 'Судьба Урзы'])

        self.e('MMQ', ['Mercadian Masques', 'MM', 'Меркадианские маски'])
        self.e('NEM', ['Nemesis', 'NE', 'NMS', 'Возмездие'])
        self.e('PCY', ['Prophecy', 'PY', 'PR', 'Пророчество'])

        self.e('INV', ['Invasion', 'IN', 'Вторжение'])
        self.e('PLS', ['Planeshift', 'PS', 'Переход через грань мира'])
        self.e('APC', ['Apocalypse', 'AP', 'Апокалипсис'])

        self.e('ODY', ['Odyssey', 'OD', 'Одиссея'])
        self.e('TOR', ['Torment', 'TO', 'TR', 'Мучения'])
        self.e('JUD', ['Judgment', 'JU', 'Judgement', 'Судилище'])

        self.e('ONS', ['Onslaught', 'ON', 'Натиск'])
        self.e('LGN', ['Legions', 'Легионы'])
        self.e('SCG', ['Scourge', 'SC', 'Бич'])

        self.e('MRD', ['Mirrodin', 'Мирродин'])
        self.e('DST', ['Darksteel', 'DS', 'Темная сталь', 'Тёмная сталь'])
        self.e('5DN', ['Fifth Dawn', 'FD', 'Пятый рассвет'])

        self.e('CHK', ['Champions of Kamigawa', 'CK', 'Чемпионы Камигавы'])
        self.e('BOK', ['Betrayers of Kamigawa', 'BK', 'Предатели Камигавы'])
        self.e('SOK', ['Saviors of Kamigawa', 'SK', 'Избавители Камигавы'])

        self.e('RAV', ['Ravnica: City of Guilds', 'Ravnica', 'RA', 'Равника: город гильдий'])
        self.e('GPT', ['Guildpact', 'GP', 'Договор Гильдий'])
        self.e('DIS', ['Dissension', 'DI', 'Раскол'])

        self.e('ICE', ['Ice Age', 'IA', 'Ледниковый период'])
        self.e('ALL', ['Alliances', 'AL', 'Союзничества'])
        self.e('CSP', ['Coldsnap', 'CS', 'Стужа'])

        self.e('TST', ['Time Spiral Timeshifted', 'TSTS', 'Timeshifted'])
        self.e('TSP', ['Time Spiral', 'TS', 'Спираль времени'])
        self.e('PLC', ['Planar Chaos', 'PC', 'PCH', 'Вселенский хаос'])
        self.e('FUT', ['Future Sight', 'FS', 'Взгляд в будущее'])

        self.e('LRW', ['Lorwyn', 'LW', 'LOR', 'Лорвин'])
        self.e('MOR', ['Morningtide', 'MT', 'Рассвет'])

        self.e('SHM', ['Shadowmoor', 'SM', 'Шэдоумур'])
        self.e('EVE', ['Eventide', 'ET', 'Сумерки'])

        self.e('ALA', ['Shards of Alara', 'SA', 'Осколки Алары'])
        self.e('CON', ['Conflux', 'CF', 'CFX', 'Слияние'])
        self.e('ARB', ['Alara Reborn', 'AR', 'Перерожденная Алара', 'Перерождённая Алара'])

        self.e('ZEN', ['Zendikar', 'Зендикар'])
        self.e('WWK', ['Worldwake', 'Пробуждение мира'])
        self.e('ROE', ['Rise of the Eldrazi', 'Возрождение эльдрази'])

        self.e('SOM', ['Scars of Mirrodin', 'Шрамы Мирродина'])
        self.e('MBS', ['Mirrodin Besieged', 'Осада Мирродина'])
        self.e('NPH', ['New Phyrexia', 'Новая Фирексия'])

        self.e('ISD', ['Innistrad', 'Иннистрад'])
        self.e('DKA', ['Dark Ascension', 'Возвышение Мрака'])
        self.e('AVR', ['Avacyn Restored', 'Возвращение Авацины'])

        self.e('RTR', ['Return to Ravnica', 'Retun to Ravnica', 'Возвращение в Равнику'])
        self.e('GTC', ['Gatecrash', 'Незваные гости'])
        self.e('DGM', ["Dragon's Maze", 'Лабиринт Дракона'])

        self.e('THS', ['Theros', 'Терос'])
        self.e('BNG', ['Born of the Gods', 'BOG', 'Порождения Богов'])
        self.e('JOU', ['Journey into Nyx', 'Путешествие в Никс'])

        self.e('KTK', ['Khans of Tarkir', 'Ханы Таркира'])
        self.e('FRF', ['Fate Reforged', 'Перекованная судьба'])
        self.e('DTK', ['Dragons of Tarkir', 'Драконы Таркира'])

        self.e('BFZ', ['Battle for Zendikar', 'Битва за Зендикар'])
        self.e('OGW', ['Oath of the Gatewatch', 'Клятва Стражей'])

        self.e('SOI', ['Shadows over Innistrad', 'Тени над Иннистрадом'])
        self.e('EMN', ['Eldritch Moon', 'Луна кошмаров'])

        self.e('KLD', ['Kaladesh', 'Каладеш'])
        self.e('AER', ['Aether Revolt', 'Эфирный бунт'])

        self.e('AKH', ['Amonkhet', 'Амонхет'])
        self.e('HOU', ['Hour of Devastation', 'Час разрушения'])

        self.e('XLN', ['Ixalan', 'Иксалан'])
        self.e('RIX', ['Rivals of Ixalan', 'Борьба за Иксалан'])

        self.e('DOM', ['Dominaria', 'Доминария'])

    def test_promo_sets(self):
        self.e('APA', ['APAC Lands', 'APAC'])
        self.e('EUL', ['European Lands'])
        self.e('GRL', ['Guru Lands'])
        self.e('VGP', ['Video Game Promos'])
        self.e('URC', ['Ultra Rare Cards'])
        self.e('THG', ['Two-Headed Giant Promos', '2HG', 'Two-Headed Giant Tournament'])
        self.e('SUM', ['Summer of Magic Promos', 'Summer of Magic', 'pSUM'])
        self.e('MSP', [
            'Book Inserts',
            'Buy-a-Box Promos',
            'Comic Inserts',
            'Convention Promos',
            'Draft Weekend Promos',
            'Full Box Promotion',
            'Magazine Inserts',
            'Misc Promos',
            'Open House Promos',
            'Other Cards',
            'Standard Showdown Promos',
            'Store Championship Promos',
            'Stores Promos',
            'Unique and Miscellaneous Promos',
            'WotC Online Store',
        ])
        self.e('PRL', [
            'Launch Party',
            'Magic: The Gathering Launch Parties',
            'pLPA',
            'pPRE',
            'pREL',
            'Prerelease & Release Cards',
            'Prerelease Events',
            'Prerelease Promos',
            'PreRelease',
            'Prerelease, Release & Launch Party Cards',
            'Release & Launch Parties Promos',
            'Release & Prerelease cards',
            'Release Events',
            'Release',
        ])
        self.e('RED', ['Redemption Program Cards'])
        self.e('MPH', ['Magic Premiere Shop'])
        self.e('MPR', ['Magic Player Rewards', 'Reward cards', 'Textless Player Rewards', 'Player Rewards', 'pMPR'])
        self.e('MGD', ['Magic Game Day Cards', 'Magic Game Day', 'Game Day', 'Game Day Promos', 'pMGD', 'Game Day'])
        self.e('JSS', ['Junior Super Series', 'Junior Series Promos', 'Junior Super Series (JSS)', 'Super Series'])
        self.e('JRW', ['Judge Rewards', 'Judge Gift Cards', 'Judge Gift Program', 'Judge Promo Cards', 'pJGP'])
        self.e('INP', ['Intro Pack Promos'])
        self.e('HGB', ['Holiday Gift Box Promos'])
        self.e('HJP', ['Hobby Japan Commemorative Cards'])
        self.e('HHL', ['Happy Holidays Promos', 'Happy Holidays'])
        self.e('WPN', ['WPN\\Gateway', 'WPN/Gateway', 'Gateway & WPN Promos', 'Wizards Play Network', 'Gateway', 'Gateway Promo', 'pWPN', 'pGTW'])
        self.e('FNM', ['Friday Night Magic', 'Friday Night Magic Promos', 'Friday Night Magic (FNM)', 'pFNM', 'FNM Promos'])
        self.e('DLM', ['DCI Legend Membership'])
        self.e('CHP', ['Champs Promos', 'Champs Promo', 'Champs', 'Tournament Promos'])
        self.e('WMC', ['World Magic Cup Qualifiers Promos', 'World Magic Cup Qualifiers', 'WMCQ', 'pWCQ'])
        self.e('PRO', ['Pro Tour Promos', 'Pro Tour'])
        self.e('GPX', ['Grand Prix Promos', 'Grand Prix Promo', 'Grand Prix'])
        self.e('WLD', ['Championships Prizes'])
        self.e('ARL', ['Arena League', 'Arena', 'Arena/Colosseo Leagues Promos', 'Arena Promo'])
        self.e('LND', ['Alternate Art Lands'])
        self.e('UGF', ["Ugin's Fate Promos", "Ugin's Fate", 'FRF_UGIN', "Ugin's Fate ugin"])
        self.e('HPP', ["Hero's Path Promos"])
        self.e('CPP', ['Clash Pack Promos', 'Clash Pack'])
        self.e('MBP', ['Media Inserts', 'Media Promos', 'pMEI'])
        self.e('TDP', ['Tarkir Dragonfury Promos'])

    def test_special_sets(self):
        self.e('AST', ['Astral'])
        self.e('BTC', ['Box Topper Cards'])

        self.e('CEI', ['Collectors Edition (International)'])
        self.e('CED', ['Collectors Edition (Domestic)'])

        self.e('REN', ['Renaissance'])
        self.e('CHR', ['Chronicles'])

        self.e('ITP', ['Introductory Two-Player Set'])
        self.e('POR', ['Portal', 'P1'])
        self.e('PO2', ['Portal: Second Age', 'Portal Second Age', 'P2'])
        self.e('S99', ['Starter 1999', 'Starter'])
        self.e('PTK', ['Portal: Three Kingdoms', 'Portal Three Kingdoms', 'P3'])
        self.e('S00', ['Starter 2000'])

        self.e('P96', ['1996 Pro Tour Decks'])
        self.e('W97', ['1997 World Championship Decks'])
        self.e('W98', ['1998 World Championship Decks'])
        self.e('W99', ['1999 World Championship Decks'])
        self.e('W00', ['2000 World Championship Decks'])
        self.e('W01', ['2001 World Championship Decks'])
        self.e('W02', ['2002 World Championship Decks'])
        self.e('W03', ['2003 World Championship Decks'])
        self.e('W04', ['2004 World Championship Decks'])

        self.e('SME', ['Salvat Magic Encyclopedia'])
        self.e('S11', ['Salvat 2011'])

        self.e('H09', ['Premium Deck Series: Slivers', 'Premium Deck: Slivers', 'PD: Slivers'])
        self.e('PD2', ['Premium Deck Series: Fire and Lightning', 'Premium Deck Series: Fire & Lightning', 'Premium Deck: Fire and Lightning', 'Premium Deck: Fire & Lightning', 'PD: Fire and Lightning', 'PD: Fire & Lightning'])
        self.e('PD3', ['Premium Deck Series: Graveborn', 'Premium Deck: Graveborn', 'PD: Graveborn'])

        self.e('CD1', ['Challenge Deck: Face the Hydra'])
        self.e('CD2', ['Challenge Deck: Battle the Horde'])
        self.e('CD3', ['Challenge Deck: Defeat a God'])

        self.e('VNG', ['Vanguard'])
        self.e('MGB', ['Multiverse Gift Box'])
        self.e('ATH', ['Anthologies'])
        self.e('BRB', ['Battle Royale Box Set', 'Battle Royal', 'Battle Royale'])
        self.e('BTD', ['Beatdown Box Set', 'Beatdown'])
        self.e('DKM', ['Deckmasters'])
        self.e('CTD', ['Coldsnap Theme Decks', 'Coldsnap Reprints'])
        self.e('DPA', ['Duels of the Planeswalkers'])
        self.e('MD1', ['Modern Event Deck', 'Modern Event Deck 2014', 'Magic Modern Event Deck'])

        self.e('CP1', ['Magic 2015 Clash Pack'])
        self.e('CP2', ['Fate Reforged Clash Pack'])
        self.e('CP3', ['Magic Origins Clash Pack'])

        self.e('CNS', ['Conspiracy'])
        self.e('CN2', ['Conspiracy: Take the Crown'])

        self.e('HOP', ['Planechase'])
        self.e('PC2', ['Planechase 2012', 'Planechase 2012 Edition'])
        self.e('PCA', ['Planechase Anthology'])

        self.e('W16', ['Welcome Deck 2016'])
        self.e('W17', ['Welcome Deck 2017'])

        self.e('EXP', ['Zendikar Expeditions', 'Zendikar Expedition'])
        self.e('MS1', ['Masterpiece Series: Kaladesh Inventions', 'Kaladesh Inventions', 'MPS_KLD'])
        self.e('MS2', ['Masterpiece Series: Amonkhet Invocations', 'Amonkhet Invocations', 'MPS_AKH'])

        self.e('ARC', ['Archenemy'])
        self.e('E01', ['Archenemy: Nicol Bolas'])

        self.e('OVS', ['Oversized Cards', 'Oversize Cards'])
        self.e('CMD', ['Commander', 'Magic: The Gathering Commander', 'Commander 2011'])
        self.e('CM1', ["Commander's Arsenal", "Commander's Aresnal"])
        self.e('C13', ['Commander 2013', 'Commander 2013 Edition'])
        self.e('C14', ['Commander 2014', 'Commander 2014 Edition'])
        self.e('C15', ['Commander 2015', 'Commander 2015 Edition'])
        self.e('C16', ['Commander 2016', 'Commander 2016 Edition'])
        self.e('CMA', ['Commander Anthology'])
        self.e('C17', ['Commander 2017', 'Commander 2017 Edition'])
        self.e('CM2', ['Commander Anthology Volume II', 'Commander Anthology Volume 2'])

        self.e('DRB', ['From the Vault: Dragons', 'FTV: Dragons'])
        self.e('V09', ['From the Vault: Exiled', 'FTV: Exiled'])
        self.e('V10', ['From the Vault: Relics', 'FTV: Relics'])
        self.e('V11', ['From the Vault: Legends', 'FTV: Legends', 'FVL'])
        self.e('V12', ['From the Vault: Realms', 'FTV: Realms'])
        self.e('V13', ['From the Vault: Twenty', 'FTV: Twenty'])
        self.e('V14', ['From the Vault: Annihilation', 'FTV: Annihilation'])
        self.e('V15', ['From the Vault: Angels', 'FTV: Angels'])
        self.e('V16', ['From the Vault: Lore', 'FTV: Lore'])
        self.e('V17', ['From the Vault: Transform', 'FTV: Transform'])

        self.e('SS1', ['Signature Spellbook: Jace'])

        self.e('E02', ['Explorers of Ixalan', 'Исследователи Иксалана'])

        self.e('UGL', ['Unglued', 'UG'])
        self.e('UNH', ['Unhinged', 'UH'])
        self.e('UST', ['Unstable'])

        self.e('MMA', ['Modern Masters'])
        self.e('MM2', ['Modern Masters 2015', 'Modern Masters 2015 Edition', 'MM2015'])
        self.e('EMA', ['Eternal Masters'])
        self.e('MM3', ['Modern Masters 2017', 'Modern Masters 2017 Edition', 'MM2017'])
        self.e('IMA', ['Iconic Masters'])
        self.e('A25', ['Masters 25'])

        self.e('EVG', ['Duel Decks: Elves vs. Goblins', 'EVG2', 'Elves vs. Goblins', 'DD3_EVG'])
        self.e('DD2', ['Duel Decks: Jace vs. Chandra', 'Jace vs. Chandra', 'DD3_JVC'])
        self.e('DDC', ['Duel Decks: Divine vs. Demonic', 'Divine vs. Demonic', 'DVD', 'DD3_DVD'])
        self.e('DDD', ['Duel Decks: Garruk vs. Liliana', 'Garruk vs. Liliana', 'GVL', 'GVL2', 'DD3_GVL'])
        self.e('DDE', ['Duel Decks: Phyrexia vs. the Coalition', 'Phyrexia vs. the Coalition'])
        self.e('DDF', ['Duel Decks: Elspeth vs. Tezzeret', 'Elspeth vs. Tezzeret'])
        self.e('DDG', ['Duel Decks: Knights vs. Dragons', 'Knights vs. Dragons'])
        self.e('DDH', ['Duel Decks: Ajani vs. Nicol Bolas', 'Ajani vs. Nicol Bolas'])
        self.e('DDI', ['Duel Decks: Venser vs. Koth', 'Venser vs. Koth'])
        self.e('DDJ', ['Duel Decks: Izzet vs. Golgari', 'Izzet vs. Golgari'])
        self.e('DDK', ['Duel Decks: Sorin vs. Tibalt', 'Sorin vs. Tibalt'])
        self.e('DDL', ['Duel Decks: Heroes vs. Monsters', 'Heroes vs. Monsters'])
        self.e('DDM', ['Duel Decks: Jace vs. Vraska', 'Jace vs. Vraska'])
        self.e('DDN', ['Duel Decks: Speed vs. Cunning', 'Speed vs. Cunning'])
        self.e('DD3', ['Duel Decks: Anthology'])
        self.e('DAE', ['Duel Decks Anthology: Elves vs. Goblins', 'Duel Decks: Elves vs. Goblins (Anthology)'])
        self.e('DAJ', ['Duel Decks Anthology: Jace vs. Chandra', 'Duel Decks: Jace vs. Chandra (Anthology)'])
        self.e('DAD', ['Duel Decks Anthology: Divine vs. Demonic', 'Duel Decks: Divine vs. Demonic (Anthology)'])
        self.e('DAG', ['Duel Decks Anthology: Garruk vs. Liliana', 'Duel Decks: Garruk vs. Liliana (Anthology)'])
        self.e('DDO', ['Duel Decks: Elspeth vs. Kiora', 'Elspeth vs. Kiora', 'Duel Decks: Kiora vs. Elspeth'])
        self.e('DDP', ['Duel Decks: Zendikar vs. Eldrazi', 'Zendikar vs. Eldrazi'])
        self.e('DDQ', ['Duel Decks: Blessed vs. Cursed', 'Blessed vs. Cursed'])
        self.e('DDR', ['Duel Decks: Nissa vs. Ob Nixilis', 'Nissa vs. Ob Nixilis'])
        self.e('DDS', ['Duel Decks: Mind vs. Might', 'Mind vs. Might'])
        self.e('DDT', ['Duel Decks: Merfolk vs. Goblins', 'Merfolk vs. Goblins'])
        self.e('DDU', ['Duel Decks: Elves vs. Inventors', 'Elves vs. Inventors'])

        self.e('BBD', ['Battlebond'])


if __name__ == '__main__':
    unittest.main()
