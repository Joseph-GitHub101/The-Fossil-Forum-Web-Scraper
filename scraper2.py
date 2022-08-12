import requests
import os
from tqdm import tqdm
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse
import re
from timeit import default_timer as timer

#headers = {"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}


def fossil_id_webpages(number_webpages):
    
    url_list = ["http://www.thefossilforum.com/index.php?/forum/14-fossil-id/"]

    for i in range(2, number_webpages):
        page = "http://www.thefossilforum.com/index.php?/forum/14-fossil-id/page/"
        page = page + str(i) + "/"
        url_list.append(page)
        
    return nj_url_list(url_list)

def nj_url_list(url_list):
    keywords = ["new-jersey", "nj", "jersey", "big-brook", "raritan", "magothy", "merchantville", "woodbury", "englishtown", "marshalltown", "wenonah", "mount-laurel", "mt-laurel", "navesink", "red-bank", "tinton", "new-egypt", "monmouth-co", "monmouth-county", "ramanessin", "hop-brook", "willow-brook", "c-and-d"]
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
        if bool(parsed.scheme) and bool(parsed.netloc) and response.headers.get('content-type') in valid_http_header_content_type:
            validated_image_links.append(i)
            
    return validated_image_links
        

def get_all_links(soup):
    """    
    Extract all the links on this section of the webpage: get all the anchor tags with the href links
    from within the p tags.    
    """
    return validated_images([tag['href'] for tag in soup.select('p a[href]')])


def download(url, pathname):
    """
    Download the image located at the given URL into the specified location
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
   
    return file_size
    '''       
    with open(pathname, 'wb') as f:
        f.write(filename)
    '''
        

def main(path):
    
    start = timer()
    
    print("Extracting all NJ image URL links...\n")
    # get all nj urls
    nj_urls = fossil_id_webpages(8)
    
    print("Starting file download...\n")
    number_of_pics_downloaded = 0
    for url in nj_urls:
        soup = get_request(url)
        final_imgs = get_all_links(soup)
        
        download_size = 0
        for img in final_imgs:
            download_size += download(img, path)
            number_of_pics_downloaded += 1
            
    end = timer()
    print("\n\nExtraction and download of " + str(number_of_pics_downloaded) + " photos (" + str(download_size) + "mB) completed in " + str(round(end-start, 2)) + " seconds.")
        
main("forum")