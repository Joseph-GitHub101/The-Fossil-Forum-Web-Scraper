import requests
import os
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse
#from tqdm import tqdm
import re

url = "http://www.thefossilforum.com/index.php?/topic/116876-monmouth-county-cretaceous-revisited-re-classification-to-plioplatecarpine/"

def get_request(url):
    """
    Obtain the soup of a single TFF topic
    """
    soup = bs(requests.get(url).content, "html.parser")
    return soup.find("div", {"id":"elPostFeed"})


def get_all_links(soup):
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
       
    # pass a list of the links to validated_images
    return validated_images(list(links))


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
        # that the content type is an image, as well as that the image URL is not that of an emoticon
        if bool(parsed.scheme) and bool(parsed.netloc) and (response.headers.get('content-type') in valid_http_header_content_type) and re.search(('emoticons'), str(i)) == None:
            validated_image_links.append(i)
            
    return validated_image_links


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
        
        if response.status_code == 200:
            f.write(response.content)
         
            
def main(url, path):
    soup = get_request(url)
    final_imgs = get_all_links(soup)
    
    print("Starting file download...\n")
    for img in final_imgs:
        download(img, path)
    print("Download complete.")

        
main(url, "forum")



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



# progress bar, changing the unit to bytes instead of iteration (default by tqdm)
progress = tqdm(response.iter_content(1024), f"Downloading {filename}", unit="B", unit_scale=True, unit_divisor=1024)

with open(filename, "wb") as f:
    for data in progress.iterable:
        # write data read to the file
        f.write(data)
        # update the progress bar manually
        progress.update(len(data))
'''         