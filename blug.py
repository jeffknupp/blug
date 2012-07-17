"""Static blog generator"""

import jinja2
import markdown
import os
import yaml
import datetime
import shutil
import argparse

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

POST_SKELETON="""
title: "{title}"
date: {date}
comments: true
categories: 
---
"""


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
    content_dir = os.path.join(os.getcwd(), 'content')
    output_dir = os.path.join(os.getcwd(), 'generated')
    template_dir = os.path.join(os.getcwd(), 'templates')
    input_files = os.listdir(content_dir)

    all_posts = get_all_posts(input_files, content_dir)
    all_posts.sort(key=lambda i: i['date'], reverse=True)
    template_variables['site']['recent_posts'] = all_posts[:5]

    for index, post in enumerate(all_posts):
        if not post['body']:
            raise EnvironmentError('No content for post [{post}] found.'.format(post=post['relative_url']))
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

def create_post(title):        
    """Create an empty post with the YAML front matter generated"""
    post_file_date = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d-')
    post_date = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d %H:%M')
    
    post_file_name = post_file_date + '-'.join(str.split(title)) + '.markdown'
    content_dir = os.path.join(os.getcwd(), 'content')
    if os.path.exists(os.path.join(content_dir, post_file_name)):
        raise EnvironmentError('[{post}] already exists.'.format(post=post_file_name))
    with open(os.path.join(content_dir, post_file_name), 'w') as post_file:
        post_file.write(POST_SKELETON.format(date=post_date, title=title))


def copy_static_content():
    """Copy (if necessary) the static content to the appropriate directory"""

    shutil.copytree('static', os.path.join(os.getcwd(), 'generated', 'static')) 

if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser(description='Generate a static HTML blog from Markdown blog entries')
    command_group = argument_parser.add_mutually_exclusive_group()
    command_group.add_argument('-p, --post', action='store', dest='post_title', help=
            'Create a new post with the title of this option\'s argument')
    command_group.add_argument('-g, --generate', dest='generate', action='store_true', help=
            'Generate the complete static site using the posts in the \'content\' directory')
    arguments = argument_parser.parse_args()

    argument_dict = vars(arguments)
    print (argument_dict)
    if 'post_title' in argument_dict and argument_dict['post_title'] != False:
        print ('Creating post...')
        create_post(argument_dict['post_title'])
    elif 'generate' in argument_dict and argument_dict['generate'] == True:
        print ('Generating...')
        site_config = yaml.load(open('config.yml', 'r').read())
        if os.path.exists(os.path.join(os.getcwd(), 'generated')):
            shutil.rmtree(os.path.join(os.getcwd(), 'generated'))
        os.mkdir(os.path.join(os.getcwd(), 'generated'))

        generate_files(site_config)
        copy_static_content()
