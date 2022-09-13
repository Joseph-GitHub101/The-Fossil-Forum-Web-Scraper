import requests
import os
from bs4 import BeautifulSoup as bs
#from urllib.parse import urlparse
import re
from collections import OrderedDict
from timeit import default_timer as timer
import sys
import time
import random
import string


def tff_webpages(numWebpages, path):
    """
    Constructs a list of all the webpage urls that will be searched for NJ topics based on the
    selected sub-forum on the fossil forum. This list is then passed to the nj_url_list function
    """
    webpage_types = {"General Fossil Discussion":"7-general-fossil-discussion/", "Fossil Hunting Trips":"20-fossil-hunting-trips/", "Fossil ID":"14-fossil-id/", "Paleo Partners":"188-partners-in-paleontology-member-contributions-to-science/", "Member Collections":"4-member-collections/", "trades":"189-member-fossil-trades-bulletin-board/", "documents":"85-documents/"}
    domain = "http://www.thefossilforum.com/index.php?/forum/"
    
    full_url = domain + webpage_types[path]
    url_list = [full_url]

    # add the number of webpages requested
    for i in range(2, numWebpages + 1):
        next_page = full_url
        next_page = next_page + "page/" + str(i) + "/"
        url_list.append(next_page)
        
    return nj_url_list(url_list)

def nj_url_list(url_list):
    """
    Constructs a list of all the urls of the NJ topics I am interested in (based on keywords) out of
    the list of urls coming from the tff_webpages function.
    """
    keywords = ["new-jersey", "nj", "jersey", "big-brook", "raritan", "magothy", "merchantville", "woodbury", "englishtown", "marshalltown", "wenonah", "mount-laurel", "mt-laurel", "navesink", "red-bank", "tinton", "new-egypt", "monmouth-co", "monmouth-county", "ramanessin", "hop-brook", "willow-brook", "c-and-d", "cooper-river", "timber-creek", "ralph-johnson", "maps", "acp", "atlantic-coastal-plain"]
    nj_urls = OrderedDict()
    
    # loop through each page of topics in the subforum
    for i in url_list:
        # select all the content inside of anchor tags of forum topics on a single webpage
        req = requests.get(i)
        soup = bs(req.content, "html.parser")
        soup2 = soup.find("div", class_="ipsBox ipsResponsive_pull")
        soup3 = soup2.find("ol")
        links = soup3.select("a")
        
        temp_urls = set()
        
        # loop through each link on the subforum webpage
        for link in links:
            # only use the href links to speed up the filtering process
            link = str(link.get('href'))
            
            # filter out some links that are irrelevant
            if re.search(('topic'), link) != None and re.search(('getLastComment'), link) == None:
                # get rid of duplicate links by removing the #comments (some links have that, some don't)
                link = link.replace('#comments', '')

                # if at least 1 keyword is contained in the url/topic title, then add it to the set
                for j in keywords:
                    if j in link:
                        temp_list = []
                        temp_list.append(link)
                        # temp_urls represents the set of all relevant links on a particular subforum webpage
                        temp_urls.update(temp_list)
                        break
        
        # A dict is needed to group together all the pages of topics with multiple pages. This will
        # be useful later when I need to group together images from one topic, as it will prevent
        # duplicates if someone quotes a photo from the first page in the second page.
        # I use the OrderedDict nj_urls instead of just using a regular dict on all the subforum topics
        # so that the order of the topics is mostly preserved in file explorer (the only possible time it
        # wouldn't be preserved is when there are >=2 relevant topics on a webpage of the subforum,
        # but that is fairly irrelevant since topics on the same webpage would have been posted around the same time).
        for k in temp_urls:
            k = k.split("page/")[0]
            if k in nj_urls:
                nj_urls[k] += 1
            else:
                nj_urls[k] = 1
        
    return nj_urls


def hms(seconds):
    '''
    Converts seconds to hours, minutes, seconds through the use of floor division and remainders
    '''
    h = seconds // 3600
    m = seconds % 3600 // 60
    s = seconds % 3600 % 60
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)
                    

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
            # find the "img" tags, which have the thumbnail class "ipsImage ipsImage_thumbnailed"
            # this will find all the pics, even if there are no full-size pics available.
            # *Note: this avoids the images that are corrupted which have the 
            # class called "ipsImage_thumbnailed". This means that the try-except block
            # in the validated_images function might not be needed. In fact, that entire function
            # is likely not needed. However, this will also ignore some pictures with external
            # links, but I don't care about those, since they aren't actually part of the forum.
            pics = p_tag.findAll('img', class_ = 'ipsImage ipsImage_thumbnailed')
            
            if len(pics) != 0:
                
                # loop through all the pics
                for i in pics:
                    # if a pic has a parent "a" tag, then we get the href link from the parent
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
                
    
    # pass a list of the links to validated_images, but make sure to take the set of the links before
    # that in order to prevent duplicate links, such as when someone quotes a post with photos in it
    return list(set(links))


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


def main(numWebpages, path):
    
    start = timer()
    
    print("Extracting all NJ image URL links...\n")
    
    # get all nj urls
    nj_urls = tff_webpages(numWebpages, path)
    
    if len(nj_urls) == 0:
        print("There aren't any NJ topics in this set of webpages. Exiting...")
        sys.exit(0)
    
    print("Downloading files...\n")
    
    number_of_pics_downloaded = 0
    for topic_url, num_pages in nj_urls.items():
        split_url = topic_url.split("topic/")[-1]
        
        # use a set to eliminate any duplicate images across multiple pages of a topic
        final_img_urls = set()
        # iterate over all the pages in the topic
        for i in range(1, num_pages + 1):
            if i == 1:
                soup = get_request(topic_url)
                    
            else:
                soup = get_request(topic_url + "page/" + str(i) + "/")
            
            final_img_urls.update(get_all_image_links(soup))
        
        # create the new file path
        file_path = os.path.join(path, split_url)
        
        for img_url in final_img_urls:
            # use a random string of 15 characters chosen from a total of 62 unique characters,
            # 62^15 = ~7.7 x 10^26 combos, so that each photo file has a unique name.
            # this prevents file explorer from overwriting images which have the same name, which would
            # happen if a topic has multiple pages and I numbered the pictures 1, 2,..., on each page. 
            photo_id = ''.join(random.choices(string.digits + string.ascii_uppercase + string.ascii_lowercase, k=15))
            # perform a download call, passing in the url of the image to be downloaded,
            # its folder path, and the photo's id.jpg
            download(img_url, file_path, photo_id + ".jpg")
            
            # increment the total number of downloaded photos
            number_of_pics_downloaded += 1
            
            # in order to bypass server request limits, I will pause the program for
            # 10 seconds after every 200 downloaded pics
            if number_of_pics_downloaded % 200 == 0:
                time.sleep(10)
            
    end = timer()
    
    total_seconds = round(end-start)
    
    print("Extraction and download of " + str(number_of_pics_downloaded) + " photos completed in " + hms(total_seconds))

# E.g. - to scrape the first 10 pages, enter 10. *Note: to scrape more than the 1st page, enter values >=2.
main(numWebpages = 4, path = "Member Collections")