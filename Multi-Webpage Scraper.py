import requests
import os
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse
import re
from timeit import default_timer as timer
import sys


def tff_webpages(numWebpages, path):
    
    webpage_types = {"General Fossil Discussion":"7-general-fossil-discussion/", "Microfossils":"178-micro-paleontology/", "Fossil Hunting Trips":"20-fossil-hunting-trips/", "Fossil ID":"14-fossil-id/", "paleo partners":"188-partners-in-paleontology-member-contributions-to-science/", "Member Collections":"4-member-collections/", "trades":"189-member-fossil-trades-bulletin-board/", "sales":"16-member-to-member-fossil-sales/", "documents":"85-documents/", "NJ Topics":"120-new-jersey/"}
    domain = "http://www.thefossilforum.com/index.php?/forum/"
    
    full_url = domain + webpage_types[path]
    url_list = [full_url]

    for i in range(2, numWebpages + 1):
        next_page = full_url
        next_page = next_page + "page/" + str(i) + "/"
        url_list.append(next_page)
        
    return nj_url_list(url_list)

def nj_url_list(url_list):
    keywords = ["new-jersey", "nj", "jersey", "big-brook", "raritan", "magothy", "merchantville", "woodbury", "englishtown", "marshalltown", "wenonah", "mount-laurel", "mt-laurel", "navesink", "red-bank", "tinton", "new-egypt", "monmouth-co", "monmouth-county", "ramanessin", "hop-brook", "willow-brook", "c-and-d", "cooper-river", "timber-creek", "ralph-johnson", "maps", "acp", "atlantic-coastal-plain"]
    nj_urls = []
    
    for i in url_list:
        req = requests.get(i)
        soup = bs(req.content, "html.parser")
        soup2 = soup.find("div", class_="ipsBox ipsResponsive_pull")
        soup3 = soup2.find("ol")
        links = soup3.select("a")
        
        for link in links:
            if re.search(('topic'), str(link)) != None and re.search(('getLastComment'), str(link)) == None and re.search(('\D/#comments'), str(link)) == None:
                
                for i in keywords:
                    if i in str(link):
                        nj_urls.append(link.get('href'))
                        break
    return nj_urls
                    

def get_request(url):
    """
    Obtain the soup that is needed
    """
    soup = bs(requests.get(url).content, "html.parser")
    return soup.find("div", {"id":"elPostFeed"})


def validated_images(urls):
    """
    Extract the valid image URLs
    """
    # valid types of content types: various images
    valid_http_header_content_type = ["image/gif", "image/jpeg", "image/png"]
    
    validated_image_links = []
    for i in urls:
        # make a head request
        response = requests.head(i)
        
        # parse each url into the 6 components
        parsed = urlparse(i)
        
        # make sure that both the scheme and netloc parts of the URL are present,
        # as well as that the content type is an image
        if bool(parsed.scheme) and bool(parsed.netloc) and (response.headers.get('content-type') in valid_http_header_content_type) and re.search(('emoticons'), str(i)) == None:
            validated_image_links.append(i)
            
    return validated_image_links
        

def get_all_links(soup):
    """    
    Extract all the links on this section of the webpage: href/src links
    from within the p tags 
    """
    links = []
    
    # use css selectors to find the pictures which are not inside of anchor tags
    no_anchors = soup.select('p:not(:has(a))')
    # find the src attribute for pics which have been added through editing
    links.extend(re.findall('src="(.*?)"', str(no_anchors)))

    # add all the picture links that are in the anchor tags
    links.extend([tag['href'] for tag in soup.select('p a[href]')])
       
    return validated_images(list(set(links)))


def download(img_url, file_path):
    """
    Download the image located at the given URL into the specified location
    """
    # if path doesn't exist, make that path dir
    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    
    # create the file name
    filename = os.path.join(file_path, img_url.split("/")[-1])
    
    with open(filename, 'wb') as f:
        # download the response body by chunk, not immediately
        response = requests.get(img_url, stream = True)
        
        #if response.status_code == 200:
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
    
    print("Starting file download...\n")
    
    number_of_pics_downloaded = 0
    for url in nj_urls:
        soup = get_request(url)
        final_img_urls = get_all_links(soup)
        
        split_url = url.split("topic/")[-1]
        if "page/" in split_url:
            split_url = split_url.split("page/")[0]
        
        file_path = os.path.join(path, split_url)
        
        for img_url in final_img_urls:
            download(img_url, file_path)
            number_of_pics_downloaded += 1
            
    end = timer()
    
    total_seconds = round(end-start)
    
    print("\nExtraction and download of " + str(number_of_pics_downloaded) + " photos completed in " + hms(total_seconds))

# E.g. - to scrape the first 10 pages, enter 10. *Note: to scrape more than the 1st page, enter values >2.
main(numWebpages = 37, path = "Fossil Hunting Trips")


# need to find a way to scrape member Albums and sub-forums that are only visible when logged in, such as NJ topics