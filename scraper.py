import requests
import os
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse
import re


url = "https://www.thefossilforum.com/index.php?/topic/41022-a-few-summer-trips-to-the-late-cretaceous-of-nj/#comments"
url2 = 'http://www.thefossilforum.com/index.php?/topic/125402-fossils-of-big-brook-in-nj/'
url3 = 'http://www.thefossilforum.com/index.php?/topic/125224-fossils-of-big-brook-in-nj/'
url4 = "http://www.thefossilforum.com/index.php?/topic/124985-interesting-big-brook-find/"


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
        if bool(parsed.scheme) and bool(parsed.netloc) and response.headers.get('content-type') in valid_http_header_content_type:
            validated_image_links.append(i)
            
    return validated_image_links
        
'''
def extract_image_tags(soup):
    """
    Extract all the image URLs on this section of the webpage
    """
    image_urls=[]
    # find all images
    for img in soup.find_all("img"):
        # make sure the image has the src attribute which has the URL and that it has the
        # keyword "monthly", since all the posts I am interested in have that keyword.
        if img.attrs.get("src") is not None and re.search(("monthly"), str(img)):
            # remove "_thumb", since this leads to a very small thumbnail version of the pic.
            image_urls.append(img.attrs.get("src").replace("_thumb", ""))
    #print(image_urls)       
    return image_urls
'''

def get_all_links(soup):
    """    
    Extract all the links on this section of the webpage: get all the anchor tags with the href links
    from within the p tags.    
    """
    return validated_images([tag['href'] for tag in soup.select('p a[href]')])

'''
def links_that_are_images(image_urls, links):
    """
    Returns links that are also image URLs
    """
    
    validated_image_links = []
    # take the intersection between the two
    image_links = set(links).intersection(image_urls)
    print(image_links)
    # validate the image links
    for i in image_links:
        if validate_image(i):
            validated_image_links.append(i)
    return validated_image_links
'''

def download(url, pathname):
    """
    Downloads a file given an URL and puts it in the folder `pathname`
    """
    # if path doesn't exist, make that path dir
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
    # download the body of response by chunk, not immediately
    response = requests.get(url, stream = True)
    # get the total file size
    file_size = int(response.headers.get("Content-Length", 0))
    # get the file name
    filename = os.path.join(pathname, url.split("/")[-1])
    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(1024), f"Downloading {filename}", total=file_size, unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        for data in progress.iterable:
            # write data read to the file
            f.write(data)
            # update the progress bar manually
            progress.update(len(data))
            
            
def main(url, path):
    soup = get_request(url)
    final_imgs = get_all_links(soup)
    
    for img in final_imgs:
        download(img, path)
        
main(url, "forum")