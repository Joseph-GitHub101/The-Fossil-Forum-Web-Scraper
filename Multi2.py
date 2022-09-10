import requests
import os
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse
import re
from timeit import default_timer as timer
import sys
import time


def tff_webpages(numWebpages, path):
    """
    Constructs a list of all the webpage urls that will be searched for NJ topics based on the
    selected sub-forum on the fossil forum. This list is then passed to the nj_url_list function
    """
    webpage_types = {"General Fossil Discussion":"7-general-fossil-discussion/", "Fossil Hunting Trips":"20-fossil-hunting-trips/", "Fossil ID":"14-fossil-id/", "Paleo Partners":"188-partners-in-paleontology-member-contributions-to-science/", "Member Collections":"4-member-collections/", "trades":"189-member-fossil-trades-bulletin-board/", "sales":"16-member-to-member-fossil-sales/", "documents":"85-documents/", "NJ Topics":"120-new-jersey/"}
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
    nj_urls = []
    
    for i in url_list:
        # select all the content inside of anchor tags of forum topics on a single webpage
        req = requests.get(i)
        soup = bs(req.content, "html.parser")
        soup2 = soup.find("div", class_="ipsBox ipsResponsive_pull")
        soup3 = soup2.find("ol")
        links = soup3.select("a")

        for link in links:
            # only use the href links to speed up the filtering process
            link = str(link.get('href'))
            
            # filter out some links that are either irrelevant or duplicates
            if re.search(('topic'), link) != None and re.search(('getLastComment'), link) == None and re.search(('\D/#comments'), link) == None:
                
                # if at least 1 keyword is contained in the url/topic title, then add it to the list
                for i in keywords:
                    if i in link:
                        nj_urls.append(link)
                        break
    return nj_urls
                    

def get_request(url):
    """
    Obtain the soup of a single TFF topic
    """
    soup = bs(requests.get(url).content, "html.parser")
    return soup.find("div", {"id":"elPostFeed"})


def get_all_image_links(soup):
    """    
    Extract all the href/src links from within the p tags on a single TFF topic
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
            # that the content type is an image, as well as that the image URL is not that of an emoticon
            if bool(parsed.scheme) and bool(parsed.netloc) and (response.headers.get('content-type') in valid_http_header_content_type) and re.search(('emoticons'), str(i)) == None:
                validated_image_links.append(i)
            
    return validated_image_links
        

def download(img_url, file_path, photo_number):
    """
    Download the image located at the given URL into the specified location
    """
    # if path doesn't exist, make that path directory
    if not os.path.isdir(file_path):
        os.makedirs(file_path)

    # create the file name
    filename = os.path.join(file_path, photo_number)

    with open(filename, 'wb') as f:
        #download the response body by chunk, not immediately
        response = requests.get(img_url, stream = True)
        
        if response.status_code == 200:
            f.write(response.content)


def hms(seconds):
    '''
    Converts seconds to hours, minutes, seconds through the use of floor division and remainders
    '''
    h = seconds // 3600
    m = seconds % 3600 // 60
    s = seconds % 3600 % 60
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)


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
    for url in nj_urls:
        soup = get_request(url)
        final_img_urls = get_all_image_links(soup)
        
        split_url = url.split("topic/")[-1]
        if "page/" in split_url:
            split_url = split_url.split("page/")[0]
        
        # create the new file path
        file_path = os.path.join(path, split_url)
        
        # counter to name the photos in each folder
        photo_number = 1
        for img_url in final_img_urls:
            # perform a download call, passing in the url of the image to be downloaded,
            # its folder path, and the photo's number.jpg
            download(img_url, file_path, str(photo_number) + ".jpg")
            
            # increment the photo filename number and the total number of downloaded photos
            photo_number += 1
            number_of_pics_downloaded += 1
            
            # in order to bypass server request limits, I will pause the program for
            # 10 seconds after every 200 downloaded pics
            if number_of_pics_downloaded % 200 == 0:
                time.sleep(10)
            
    end = timer()
    
    total_seconds = round(end-start)
    
    print("Extraction and download of " + str(number_of_pics_downloaded) + " photos completed in " + hms(total_seconds))

# E.g. - to scrape the first 10 pages, enter 10. *Note: to scrape more than the 1st page, enter values >2.
main(numWebpages = 50, path = "Fossil ID")