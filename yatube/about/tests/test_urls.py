from django.test import TestCase, Client


class StaticURLTests(TestCase):

    def setUp(self) -> None:
        self.guest_client = Client()
        self.url_author = '/about/author/'
        self.url_tech = '/about/tech/'

    def test_about_author(self):
        response = self.guest_client.get(self.url_author)
        self.assertEqual(
            response.status_code, 200,
            f'Ошибка {response.status_code} '
            f'при открытиии страницы {self.url_author}.'
        )

    def test_about_tech(self):
        response = self.guest_client.get(self.url_tech)
        self.assertEqual(
            response.status_code, 200,
            f'Ошибка {response.status_code} '
            f'при открытиии страницы {self.url_author}.'
        )
