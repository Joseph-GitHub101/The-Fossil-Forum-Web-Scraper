import requests
import os
from bs4 import BeautifulSoup as bs
import re
import random
import string
#from urllib.parse import urlparse

#url = "http://www.thefossilforum.com/index.php?/topic/24122-cooper-river-dive-charter/"
#url = "http://www.thefossilforum.com/index.php?/topic/116876-monmouth-county-cretaceous-revisited-re-classification-to-plioplatecarpine/"
#url = "http://www.thefossilforum.com/index.php?/topic/25040-dino-hunting-trip-with-the-nj-state-museum-on-july-2012/"
#url = "http://www.thefossilforum.com/index.php?/topic/101415-a-few-riker-mounts-with-specimens-from-the-aquia-formation-of-maryland-and-the-nanjemoy-formation-of-virginia/"
#url = "http://www.thefossilforum.com/index.php?/topic/99130-cretaceous-new-jersey-fossils/"
url = "http://www.thefossilforum.com/index.php?/topic/101728-the-vertebra-appreciation-thread-show-some-back-bone/"

def get_request(url):
    """
    Obtain the soup of a single TFF topic
    """
    soup = bs(requests.get(url).content, "html.parser")
    return soup.find("div", {"id":"elPostFeed"})


def get_all_image_links(soup):
    """    
    Extract all the href/src image links from within the p tags on a single TFF topic
    """
    
    links = []
    
    # use the div class which corresponds to the content within the topic's posts, not the profile info, etc. on the sides
    posts = soup.find_all("div", class_ = "ipsColumn ipsColumn_fluid ipsMargin:none")
    
    # looping through the posts
    for post in posts:
        # find all images
        for p_tag in post.findAll('p'):
            if p_tag.find('img'):
                
                # find the "img" tags, which have the thumbnail class
                # this will find all the pics, even if there are no full-size pics available.
                # *Note: this avoids the images that are corrupted which have the 
                # class called "ipsImage_thumbnailed". This means that the try-except block
                # in the validated_images function might not be needed. In fact, that entire function
                # is likely not needed.
                thumbnails = p_tag.findAll('img', class_ = 'ipsImage ipsImage_thumbnailed')
                
                # loop through all the thumbnails
                for i in thumbnails:
                    # if a thumbnail has a parent "a" tag, then we get the href link from the parent
                    # the href links are the full-size pics, so that is the preference
                    if i.find_parent('a') != None:
                        href = str(i.find_parent('a').get('href'))
                        # make sure that the image URL is not that of an emoticon, reaction, profile, or award
                        if href != None and re.search(('/uploads/reactions/'), href) == None and re.search(('/uploads/emoticons/'), href) == None and re.search(('/uploads/awards/'), href) == None and re.search(('/profile/'), href) == None:
                            links.append(href)
                            
                    # if the parent with the href link doesn't exist, only then do we settle for the src thumbnail
                    else:
                        src = str(i.get('src'))
                        # make sure that the image URL is not that of an emoticon, reaction, profile, or award
                        if src != None and re.search(('/uploads/reactions/'), src) == None and re.search(('/uploads/emoticons/'), src) == None and re.search(('/uploads/awards/'), src) == None and re.search(('/profile/'), src) == None:
                            links.append(src)


                # early version: this just extracts all the img links, including duplicates
                #links.extend(re.findall('(?:src|href)=\"(.*?)\"', str(p_tag)))
                
    
    # pass a list of the links to validated_images, but make sure to take the set of the links before
    # that in order to prevent duplicate links, such as when someone quotes a post with photos in it
    return list(set(links))


def download(img_url, file_path, photo_id):
    """
    Download the image located at the given URL into the specified location
    """
    # if path doesn't exist, make that path directory
    if not os.path.isdir(file_path):
        os.makedirs(file_path)

    # create the file name
    filename = os.path.join(file_path, photo_id)

    with open(filename, 'wb') as f:
        #download the response body by chunk, not immediately
        response = requests.get(img_url, stream = True)
        f.write(response.content)

            
def main(url, path):
    soup = get_request(url)
    final_imgs = get_all_image_links(soup)
    print("Starting file download...\n")
    
    for img in final_imgs:
        # use a random string of 62 choose 15 characters (> 90 trillion combos), so that each photo file has a unique name
        photo_id = ''.join(random.choices(string.digits + string.ascii_uppercase + string.ascii_lowercase, k=15))
        # perform a download call, passing in the url of the image to be downloaded,
        # its folder path, and the photo's id.jpg
        download(img, path, photo_id + ".jpg")
        
    print("Download complete.")

        
main(url, "forum")



# old code:

'''
def get_all_image_links(soup):
    """    
    Extract all the href/src image links from within the p tags on a single TFF topic
    """
    # use a set in order to prevent duplicate links, such as when someone tags someone else's post
    links = set()
    
    # use css selectors to find the pictures which are not inside of anchor tags
    no_anchors = soup.select('p:not(:has(a))')
    # find the src attribute for pics which have been added through editing
    links.update(re.findall('src="(.*?)"', str(no_anchors)))

    # add all the picture links that are in the anchor tags
    links.update([tag['href'] for tag in soup.select('p a[href]')])
    
    # delete any set elements that contain mailto links
    links = list(filter(lambda x: 'mailto:' not in str(x), links))
       
    # pass a list of the links to validated_images
    return validated_images(links)
'''

'''
def validated_images(urls):
    """
    Extract the valid image URLs
    """
    # valid types of content types: various images
    valid_http_header_content_type = ["image/gif", "image/jpeg", "image/png"]
    
    validated_image_links = []
    for i in urls:
        try:
            # make a head request
            response = requests.head(i)
            
        except:
            # if there is a ConnectionError - when there is a broken link and the server's ip address cannot be found
            pass
        
        else:
            # parse each url into the 6 components
            parsed = urlparse(i)
            
            # make sure that both the scheme and netloc parts of the URL are present,
            # and that the content type is an image
            if bool(parsed.scheme) and bool(parsed.netloc) and (response.headers.get('content-type') in valid_http_header_content_type):
                validated_image_links.append(i)
            
    return validated_image_links
'''
'''
def download(img_url, file_path, photo_id):
    
    try:
        #download the response body by chunk, not immediately
        response = requests.get(img_url, stream = True)
        
        # if path doesn't exist, make that path directory
        if not os.path.isdir(file_path):
            os.makedirs(file_path)
        
        # create the file name
        filename = os.path.join(file_path, photo_id)
    except:
        # if there is an expired image link, this will ignore it
        pass
    else:
        with open(filename, 'wb') as f:
            f.write(response.content)
            
'''