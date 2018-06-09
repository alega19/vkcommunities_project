from django.test import SimpleTestCase

from ..wallupdater import WallUpdater


class LinksParsingTests(SimpleTestCase):

    def test_borders_of_links(self):
        text_2_link = [
            (r"""aaa.test.com""", r"""aaa.test.com"""),
            (r"""aaaяtest.com""", r"""aaaяtest.com"""),
            (r"""aaaёtest.com""", r"""aaaёtest.com"""),
            (r"""aaaґtest.com""", r"""aaaґtest.com"""),
            (r"""aaaєtest.com""", r"""aaaєtest.com"""),
            (r"""aaastest.com""", r"""aaastest.com"""),

            (r"""test.com.aaa""", r"""test.com.aaa"""),
            (r"""test.com,aaa""", r"""test.com"""),
            (r"""test.com7aaa""", None),
            (r"""test.com-aaa""", None),
            (r"""test.com_aaa""", r"""test.com"""),
            (r"""test.com/aaa""", r"""test.com/aaa"""),
            (r"""test.com\aaa""", r"""test.com"""),
            (r"""test.com+aaa""", r"""test.com"""),
            (r"""test.com=aaa""", r"""test.com"""),
            (r"""test.com*aaa""", r"""test.com"""),
            (r"""test.com;aaa""", r"""test.com"""),
            (r"""test.com:aaa""", r"""test.com"""),
            (r"""test.com"aaa""", r"""test.com"""),
            (r"""test.com'aaa""", r"""test.com"""),
            (r"""test.com`aaa""", r"""test.com"""),
            (r"""test.com~aaa""", r"""test.com"""),
            (r"""test.com!aaa""", r"""test.com"""),
            (r"""test.com@aaa""", r"""test.com"""),
            (r"""test.com#aaa""", r"""test.com#aaa"""),
            (r"""test.com№aaa""", r"""test.com"""),
            (r"""test.com$aaa""", r"""test.com"""),
            (r"""test.com%aaa""", r"""test.com"""),
            (r"""test.com^aaa""", r"""test.com"""),
            (r"""test.com&aaa""", r"""test.com"""),
            (r"""test.com?aaa""", r"""test.com?aaa"""),
            (r"""test.com<aaa""", r"""test.com"""),
            (r"""test.com>aaa""", r"""test.com"""),
            (r"""test.com(aaa""", r"""test.com"""),
            (r"""test.com)aaa""", r"""test.com"""),
            (r"""test.com[aaa""", r"""test.com"""),
            (r"""test.com]aaa""", r"""test.com"""),
            (r"""test.com{aaa""", r"""test.com"""),
            (r"""test.com}aaa""", r"""test.com"""),
            (r"""test.com|aaa""", r"""test.com"""),
            (r"""test.comйaaa""", None),
            (r"""test.comщaaa""", None),
            (r"""test.comьaaa""", None),
            (r"""test.comъaaa""", None),
            (r"""test.comыaaa""", None),
            (r"""test.comяaaa""", None),
            (r"""test.comёaaa""", r"""test.com"""),
            (r"""test.comґaaa""", r"""test.com"""),
            (r"""test.comєaaa""", r"""test.com"""),
            (r"""test.comsaaa""", None),

            (r"""test.com/.aaa""", r"""test.com/.aaa"""),
            (r"""test.com/,aaa""", r"""test.com/,aaa"""),
            (r"""test.com/7aaa""", r"""test.com/7aaa"""),
            (r"""test.com/-aaa""", r"""test.com/-aaa"""),
            (r"""test.com/_aaa""", r"""test.com/_aaa"""),
            (r"""test.com//aaa""", r"""test.com//aaa"""),
            (r"""test.com/\aaa""", r"""test.com/\aaa"""),
            (r"""test.com/+aaa""", r"""test.com/+aaa"""),
            (r"""test.com/=aaa""", r"""test.com/=aaa"""),
            (r"""test.com/*aaa""", r"""test.com/"""),
            (r"""test.com/;aaa""", r"""test.com/;aaa"""),
            (r"""test.com/:aaa""", r"""test.com/:aaa"""),
            (r"""test.com/"aaa""", r"""test.com/"aaa"""),
            (r"""test.com/'aaa""", r"""test.com/'aaa"""),
            (r"""test.com/`aaa""", r"""test.com/"""),
            (r"""test.com/~aaa""", r"""test.com/~aaa"""),
            (r"""test.com/!aaa""", r"""test.com/!aaa"""),
            (r"""test.com/@aaa""", r"""test.com/@aaa"""),
            (r"""test.com/#aaa""", r"""test.com/#aaa"""),
            (r"""test.com/№aaa""", r"""test.com/"""),
            (r"""test.com/$aaa""", r"""test.com/$aaa"""),
            (r"""test.com/%aaa""", r"""test.com/%aaa"""),
            (r"""test.com/^aaa""", r"""test.com/"""),
            (r"""test.com/&aaa""", r"""test.com/&aaa"""),
            (r"""test.com/?aaa""", r"""test.com/?aaa"""),
            (r"""test.com/<aaa""", r"""test.com/<aaa"""),
            (r"""test.com/>aaa""", r"""test.com/>aaa"""),
            (r"""test.com/(aaa""", r"""test.com/"""),
            (r"""test.com/)aaa""", r"""test.com/"""),
            (r"""test.com/[aaa""", r"""test.com/"""),
            (r"""test.com/]aaa""", r"""test.com/"""),
            (r"""test.com/{aaa""", r"""test.com/"""),
            (r"""test.com/}aaa""", r"""test.com/"""),
            (r"""test.com/|aaa""", r"""test.com/"""),
            (r"""test.com/яaaa""", r"""test.com/яaaa"""),
            (r"""test.com/ёaaa""", r"""test.com/ёaaa"""),
            (r"""test.com/ґaaa""", r"""test.com/ґaaa"""),
            (r"""test.com/єaaa""", r"""test.com/єaaa"""),
            (r"""test.com/saaa""", r"""test.com/saaa"""),

            (r"""test.com/z.aaa""", r"""test.com/z.aaa"""),
            (r"""test.com/z,aaa""", r"""test.com/z,aaa"""),
            (r"""test.com/z7aaa""", r"""test.com/z7aaa"""),
            (r"""test.com/z-aaa""", r"""test.com/z-aaa"""),
            (r"""test.com/z_aaa""", r"""test.com/z_aaa"""),
            (r"""test.com/z/aaa""", r"""test.com/z/aaa"""),
            (r"""test.com/z\aaa""", r"""test.com/z\aaa"""),
            (r"""test.com/z+aaa""", r"""test.com/z+aaa"""),
            (r"""test.com/z=aaa""", r"""test.com/z=aaa"""),
            (r"""test.com/z*aaa""", r"""test.com/z"""),
            (r"""test.com/z;aaa""", r"""test.com/z;aaa"""),
            (r"""test.com/z:aaa""", r"""test.com/z:aaa"""),
            (r"""test.com/z"aaa""", r"""test.com/z"aaa"""),
            (r"""test.com/z'aaa""", r"""test.com/z'aaa"""),
            (r"""test.com/z`aaa""", r"""test.com/z"""),
            (r"""test.com/z~aaa""", r"""test.com/z~aaa"""),
            (r"""test.com/z!aaa""", r"""test.com/z!aaa"""),
            (r"""test.com/z@aaa""", r"""test.com/z@aaa"""),
            (r"""test.com/z#aaa""", r"""test.com/z#aaa"""),
            (r"""test.com/z№aaa""", r"""test.com/z"""),
            (r"""test.com/z$aaa""", r"""test.com/z$aaa"""),
            (r"""test.com/z%aaa""", r"""test.com/z%aaa"""),
            (r"""test.com/z^aaa""", r"""test.com/z"""),
            (r"""test.com/z&aaa""", r"""test.com/z&aaa"""),
            (r"""test.com/z?aaa""", r"""test.com/z?aaa"""),
            (r"""test.com/z<aaa""", r"""test.com/z<aaa"""),
            (r"""test.com/z>aaa""", r"""test.com/z>aaa"""),
            (r"""test.com/z(aaa""", r"""test.com/z"""),
            (r"""test.com/z)aaa""", r"""test.com/z"""),
            (r"""test.com/z[aaa""", r"""test.com/z"""),
            (r"""test.com/z]aaa""", r"""test.com/z"""),
            (r"""test.com/z{aaa""", r"""test.com/z"""),
            (r"""test.com/z}aaa""", r"""test.com/z"""),
            (r"""test.com/z|aaa""", r"""test.com/z"""),
            (r"""test.com/zяaaa""", r"""test.com/zяaaa"""),
            (r"""test.com/zёaaa""", r"""test.com/zёaaa"""),
            (r"""test.com/zґaaa""", r"""test.com/zґaaa"""),
            (r"""test.com/zєaaa""", r"""test.com/zєaaa"""),
            (r"""test.com/zsaaa""", r"""test.com/zsaaa"""),

            (r"""-test.com""", r"""-test.com"""),
            (r"""_test.com""", r"""_test.com"""),
            (r"""%test.com""", r"""test.com"""),
            (r""",test.com""", r"""test.com"""),
            (r"""a.test.com""", r"""a.test.com"""),
            (r"""я.test.com""", r"""я.test.com"""),
            (r"""ё.test.com""", r"""ё.test.com"""),
            (r"""7.test.com""", r"""7.test.com"""),
            (r"""-.test.com""", r"""-.test.com"""),
            (r"""_.test.com""", r"""_.test.com"""),
            (r"""ґ.test.com""", r"""ґ.test.com"""),
            (r"""є.test.com""", r"""є.test.com"""),
            (r"""і.test.com""", r"""і.test.com"""),
            (r"""ї.test.com""", r"""ї.test.com"""),

            (r"""test@test.com""", None),

            ('\ntest.com\n', 'test.com'),
            ('\nhttps://test.com\n', 'https://test.com'),
        ]
        for text, link in text_2_link:
            found_links = WallUpdater._find_links(text)
            if link is None:
                self.assertEqual(
                    len(found_links), 0,
                    'found {0} in {1} instead nothing'.format(found_links, text))
            else:
                self.assertEqual(
                    len(found_links), 1,
                    'found {0} in {1} instead {2}'.format(found_links, text, link))
                self.assertEqual(
                    found_links[0], link,
                    'found {0} in {1} instead {2}'.format(found_links, text, link))

    def test_available_symbols_in_domain(self):
        links = [
            'abcdefghijklmnopqrstuvwxyz.com',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ.COM',
            'абвгдеёжзийклмнопрстуфхцчшщъыьэюя.рус',
            'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ.РУС',
            'ґєії.укр',
            'ҐЄІЇ.УКР',
            'AbCвДеЁжҐєІї.org',
            'тест-_.7.ru',
        ]
        for link in links:
            found_links = WallUpdater._find_links(link)
            self.assertEqual(
                len(found_links), 1,
                'found {0} in {1} instead {1}'.format(found_links, link))
            self.assertEqual(found_links[0], link)

    def test_available_symbols_in_path(self):
        link = r'''test.com/.,7-_/\+=;:"'~!@#$%&?<>яёґєsЯЁҐЄS'''
        found_links = WallUpdater._find_links(link)
        self.assertEqual(
            len(found_links), 1,
            'found {0} in {1} instead {1}'.format(found_links, link))
        self.assertEqual(found_links[0], link)

    def test_excluded_domains(self):
        links = [
            'vk.com',
            'm.vk.com',
            '0.vk.com',
        ]
        for link in links:
            found_links = WallUpdater._find_links(link)
            self.assertEqual(
                len(found_links), 0,
                'found {0} in {1} instead nothing'.format(found_links, link))

        link = 'vk.com.com'
        found_links = WallUpdater._find_links(link)
        self.assertEqual(
            len(found_links), 1,
            'found {0} in {1} instead {1}'.format(found_links, link))
        self.assertEqual(found_links[0], 'vk.com.com')
