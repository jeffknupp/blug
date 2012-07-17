import unittest
import datetime
import blug
import os
import tempfile


class TestGeneratePost(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        os.chdir(self.directory.name)
        os.mkdir(os.path.join(os.getcwd(), 'content'))

    def test_create_post_file(self):
        title = 'Test Post With Spaces'
        post_file_date = datetime.datetime.strftime(
                datetime.datetime.today(), '%Y-%m-%d-')
        post_file_name = post_file_date + '-'.join(
                str.split(title)) + '.markdown'

        blug.create_post(title)
        self.assertTrue(os.path.exists(os.path.join(os.getcwd(),
            'content', post_file_name)))

    def test_create_already_existing_post(self):
        title = 'Duplicate Post'
        blug.create_post(title)
        self.assertRaises(EnvironmentError, blug.create_post, title)

if __name__ == '__main__':
    unittest.main()
