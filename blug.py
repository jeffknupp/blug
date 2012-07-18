"""Static blog generator"""

import jinja2
import markdown
import os
import yaml
import datetime
import shutil
import argparse

# recent_posts:
# post.title
# post.author
# post.description
# post.date
# post.body
# post.canonical_url
# post_previous.relative_url
# post_previous.title
# post.relative_url
# post.canonical_url

POST_SKELETON = """
title: "{title}"
date: {date}
---
"""


def generate_post_filepath(title, date):
    """Return the path a post should use based on its title and date"""
    post_file_date = datetime.datetime.strftime(date, '%Y/%m/%d/')
    title = ''.join(char for char in title.lower() if (
        char.isalnum() or char == ' '))
    return post_file_date + title.replace(' ', '-') + '/'


def get_all_posts(content_dir, blog_prefix, canonical_url, blog_root):
    """Return a list of dictionaries representing converted posts"""
    input_files = os.listdir(content_dir)
    all_posts = list()

    for post_file_name in input_files:
        post_file_buffer = str()
        with open(os.path.join(content_dir, post_file_name), 'r') as post_file:
            post_file_buffer = post_file.read()

        (front_matter, _, post_body) = post_file_buffer.partition('\n---\n')
        post = yaml.load(front_matter)
        post['date'] = datetime.datetime.strptime(
                (post['date'].strip()), '%Y-%m-%d %H:%M')

        # Generate HTML from Markdown
        post['body'] = markdown.markdown(post_body, ['fenced_code'])
        (teaser, _, _) = post['body'].partition('<!--more-->')
        post['teaser'] = teaser
        post['relative_path'] = os.path.join(blog_prefix,
                generate_post_filepath(post['title'], post['date']))

        post['relative_url'] = os.path.join('/', blog_root,
                post['relative_path'])
        post['canonical_url'] = canonical_url + post['relative_url']

        all_posts.append(post)
    return all_posts


def create_path_to_file(path):
    """Given a path, make sure all intermediate directories exiss and
    create them if they don't"""
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def generate_post(post, template_variables):
    """Generate a single post's HTML file"""
    output_path = os.path.join(template_variables['output_dir'],
            post['relative_path'], 'index.html')

    if not post['body']:
        raise EnvironmentError('No content for post [{post}] found.'.format(
            post=post['relative_path']))
    post['description'] = post['body'].split()[0]
    post_vars = {'post': post}

    template_variables.update(post_vars)
    template = template_variables['env'].get_template('post.html')
    final_html = template.render(template_variables)
    create_path_to_file(output_path)
    open(output_path, 'w').write(final_html)


def generate_static_page(template_variables, output_dir,
        template_name='index.html'):
    """Generate static pages"""
    template = template_variables['env'].get_template(template_name)
    resulting_html = template.render(template_variables)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, 'index.html'),
            'w') as output_file:
        output_file.write(resulting_html)


def generate_files(template_variables):
    """Generate all HTML files from the template directory using the sitewide
    configuration"""
    all_posts = get_all_posts(template_variables['content_dir'],
            template_variables['blog_prefix'], template_variables['url'],
            template_variables['blog_root'])
    all_posts.sort(key=lambda i: i['date'], reverse=True)
    template_variables['recent_posts'] = all_posts[:5]
    template_variables['all_posts'] = all_posts
    template_variables['env'] = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_variables['template_dir']))
    generate_static_page(template_variables,
            template_variables['output_dir'], 'index.html')
    generate_static_page(template_variables,
            template_variables['blog_dir'], 'index.html')
    generate_static_page(template_variables,
            os.path.join(template_variables['blog_dir'],
                'archives'), 'archives.html')
    generate_static_page(template_variables,
            os.path.join(template_variables['output_dir'],
                'about-me'), 'about.html')
    current_page = 1
    for page in [all_posts[index:index + 5] for index in range(
        5, len(all_posts), 5)]:
        current_page += 1
        template_variables['all_posts'] = page
        output_dir = os.path.join(template_variables['blog_dir'],
                'page', str(current_page))
        generate_static_page(template_variables, output_dir, 'index.html')

    for index, post in enumerate(all_posts):
        post['post_previous'] = all_posts[index - 1]
        generate_post(post, template_variables)


def create_post(title, content_dir):
    """Create an empty post with the YAML front matter generated"""
    post_file_date = datetime.datetime.strftime(
            datetime.datetime.today(), '%Y %m %d')
    post_date = datetime.datetime.strftime(
            datetime.datetime.today(), '%Y-%m-%d %H:%M')

    post_file_name = os.path.join(post_file_date.split()) + '-'.join(
            str.split(title)) + '.markdown'
    if os.path.exists(os.path.join(content_dir, post_file_name)):
        raise EnvironmentError(
                '[{post}] already exists.'.format(post=post_file_name))
    with open(os.path.join(content_dir, post_file_name), 'w') as post_file:
        post_file.write(POST_SKELETON.format(date=post_date, title=title))


def copy_static_content(output_dir, root_dir):
    """Copy (if necessary) the static content to the appropriate directory"""

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        print ('Removing old content...')
    shutil.copytree(os.path.join(root_dir, 'static'), output_dir)


def main():
    """Main execution of blug"""
    argument_parser = argparse.ArgumentParser(
            description='Generate a static HTML blog from \
                    Markdown blog entries')
    command_group = argument_parser.add_mutually_exclusive_group()
    command_group.add_argument('-p, --post', action='store',
            dest='post_title', help='Create a new post with the \
                    title of this option\'s argument')
    command_group.add_argument('-g, --generate', dest='generate',
            action='store_true', help='Generate the complete static site \
                    using the posts in the \'content\' directory')
    arguments = argument_parser.parse_args()

    argument_dict = vars(arguments)

    site_config = dict()
    with open('config.yml', 'r') as config_file:
        site_config = yaml.load(config_file.read())

    site_config['root_dir'] = os.getcwd()
    site_config['blog_dir'] = os.path.join(site_config['output_dir'],
            site_config['blog_prefix'])

    if 'post_title' in argument_dict and argument_dict['post_title'] == True:
        print ('Creating post...')
        create_post(argument_dict['post_title'], site_config['content_dir'])
    elif 'generate' in argument_dict and argument_dict['generate'] == True:
        print ('Generating...')
        copy_static_content(site_config['output_dir'], site_config['root_dir'])
        generate_files(site_config)
    print ('Complete')


if __name__ == '__main__':
    main()
