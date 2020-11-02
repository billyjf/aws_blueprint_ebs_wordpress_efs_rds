from unittest import TestCase
import build


class Test(TestCase):
    def test_get_wordpress_salts(self):
        build.get_wordpress_salts()
