"""Static blog generator"""

import jinja2
import markdown
import os
import yaml
import datetime

# categories:
# recent_posts:
# post.title
# post.author
# post.description
# post.date
# post.body
# post.canconical_url
# post_previous.relative_url
# post_previous.title
# post.relative_url
# post.canonical_url


def get_all_posts(input_files, content_dir):
    """Return a list of dictionaries each of the markdown converted
    posts and its associated metadata"""
    all_posts = list()

    for post_file_name in input_files:

        post_file_buffer = str()
        with open(os.path.join(content_dir, post_file_name), 'r') as post_file:
            post_file_buffer = post_file.read()

        (front_matter, sep, post_body) = post_file_buffer.partition('\n---\n')
        post = yaml.load(front_matter)
        post['relative_url'] = post_file_name
        post['body'] = markdown.markdown(post_body, ['fenced_code'])
        post['relative_url'] = post_file_name.replace(
                os.path.splitext(post_file_name)[1], '.html')
        if 'date' in post:
            post['date'] = datetime.datetime.strptime(
                    (post['date'].strip()), '%Y-%m-%d %H:%M')

        all_posts.append(post)
    return all_posts


def generate_files(template_variables):
    """Generate all HTML files from the template directory using the sitewide
    configuration"""
    content_dir = os.path.join(os.curdir, 'content')
    output_dir = os.path.join(os.curdir, 'generated')
    template_dir = os.path.join(os.curdir, 'templates')
    input_files = os.listdir(content_dir)

    all_posts = get_all_posts(input_files, content_dir)
    all_posts.sort(key=lambda i: i['date'], reverse=True)
    template_variables['site']['recent_posts'] = all_posts[:5]

    for index, post in enumerate(all_posts):
        post['description'] = post['body'].split()[0]
        template_variables_copy = template_variables
        post['post_previous'] = all_posts[index - 1]
        post['post'] = post

        template_file_buffer = str()
        with open(os.path.join(template_dir, 'post.html'), 'r') as template_file:
            template_file_buffer = template_file.read()

        template_variables_copy.update(post)
        final_html = jinja2.Template(
                template_file_buffer).render(template_variables_copy)
        # markdown doesn't have a universally agreed upon extension, so
        # don't assume a particular one here
        open(os.path.join(output_dir,
            post['relative_url']), 'w').write(final_html)


if __name__ == '__main__':
    site_config = yaml.load(open('config.yml', 'r').read())
    generate_files(site_config)
