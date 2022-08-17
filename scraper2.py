import requests
import os
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse
import re
#from docx import Document
from timeit import default_timer as timer
import sys
#from tqdm import tqdm


#headers = {"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}


def fossil_id_webpages(numWebpages, path):
    
    webpage_types = {"General Fossil Discussion":"7-general-fossil-discussion/", "Microfossils":"178-micro-paleontology/", "Fossil Hunting Trips":"20-fossil-hunting-trips/", "Fossil ID":"14-fossil-id/", "paleo partners":"188-partners-in-paleontology-member-contributions-to-science/", "Member Collections":"4-member-collections/", "trades":"189-member-fossil-trades-bulletin-board/", "sales":"16-member-to-member-fossil-sales/", "documents":"85-documents/", "NJ Topics":"120-new-jersey/"}
    domain = "http://www.thefossilforum.com/index.php?/forum/"
    
    full_url = domain + webpage_types[path]
    url_list = [full_url]

    for i in range(2, numWebpages):
        next_page = full_url
        next_page = next_page + "page/" + str(i) + "/"
        url_list.append(next_page)
        
    return nj_url_list(url_list)

def nj_url_list(url_list):
    keywords = ["new-jersey", "nj", "jersey", "big-brook", "raritan", "magothy", "merchantville", "woodbury", "englishtown", "marshalltown", "wenonah", "mount-laurel", "mt-laurel", "navesink", "red-bank", "tinton", "new-egypt", "monmouth-co", "monmouth-county", "ramanessin", "hop-brook", "willow-brook", "c-and-d", "cooper-river", "timber-creek", "ralph-johnson"]
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


def download(img_url, file_path):
    """
    Download the image located at the given URL into the specified location
    """
    # if path doesn't exist, make that path dir
    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    
    # get the file name
    filename = os.path.join(file_path, img_url.split("/")[-1])
    
    with open(filename, 'wb') as f:
        # download the response body by chunk, not immediately
        response = requests.get(img_url, stream = True)
        
        if response.status_code == 200:
            f.write(response.content)
    
    '''
    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(1024), f"Downloading {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    
    with open(filename, "wb") as f:
        for data in progress.iterable:
            # write data read to the file
            f.write(data)
            # update the progress bar manually
            progress.update(len(data))
            #print(len(data))
    '''      
    

def main(numWebpages, path):
    
    start = timer()
    
    print("Extracting all NJ image URL links...\n")
    
    # get all nj urls
    nj_urls = fossil_id_webpages(numWebpages, path)
    
    if len(nj_urls) == 0:
        print("There aren't any NJ topics in this set of webpages. Exiting...")
        sys.exit(0)
    
    new_path = "C:/Users/19084/Desktop/The Fossil Forum/" + path
    
    print("Starting file download...\n")
    
    number_of_pics_downloaded = 0
    for url in nj_urls:
        soup = get_request(url)
        final_img_urls = get_all_links(soup)
        
        split_url = url.split("topic/")[-1]
        if "page/" in split_url:
            split_url = split_url.split("page/")[0]
        
        file_path = os.path.join(new_path, split_url)
        
        '''
        mydoc = Document()
        mydoc.add_paragraph(url)
        mydoc.save(new_path + "/webpage url.docx")
        '''
        
        
        for img_url in final_img_urls:
            download(img_url, file_path)
            number_of_pics_downloaded += 1
            
    end = timer()
    print("\nExtraction and download of " + str(number_of_pics_downloaded) + " photos completed in " + str(round(end-start, 2)) + " seconds.")

# E.g. - to scrape the first 10 pages, enter 11. *Note: to scrape more than the 1st page, enter values >2.
main(numWebpages = 15, path = "Fossil Hunting Trips")


# need to find a way to scrape member Albums and sub-forums that are only visible when logged in, such as NJ topics