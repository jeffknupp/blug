import unittest
import datetime
import blug
import os
import tempfile


class TestGeneratePost(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        os.chdir(self.directory)
        os.mkdir(os.path.join(os.getcwd(), 'content'))
        self.content_dir = os.path.join(os.getcwd(), 'content')

    def test_create_post_file(self):
        title = 'Test Post With Spaces'
        post_file_name = 'test-post-with-spaces.md'

        os.chdir(self.directory)
        blug.create_post(title, self.content_dir)
        self.assertTrue(os.path.exists(os.path.join(
            self.content_dir,
            post_file_name)))

    def test_create_already_existing_post(self):
        title = 'Duplicate Post'
        blug.create_post(title, self.content_dir)
        self.assertRaises(EnvironmentError, blug.create_post, title, self.content_dir)

if __name__ == '__main__':
    unittest.main()
